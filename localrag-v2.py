import torch
import ollama
import os
from openai import OpenAI
import argparse
import re
import json
from time import perf_counter
import sys

# ANSI escape codes for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'


#inputs
"""
if (len(sys.argv) < 3) :
    print("INPUTS: <process_train_file> <TRs_file> ")
    print("e.g. >python localrag-v2.py development-process.json input_for_localAI.json")
    exit()

process_file = sys.argv[1]
tr_file = sys.argv[2]
print("INPUT: process train file: ",process_file)
print("INPUT: TRs file: ",tr_file)
"""

process_file = "dev-process.json"
tr_file = "input_for_localAI_2TR.json"

# Function to open a file and return its contents as a string
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Function to get relevant context from the vault based on user input
def get_relevant_context(rewritten_input, vault_embeddings, vault_content, top_k=3):
    if vault_embeddings.nelement() == 0:  # Check if the tensor has any elements
        return []
    # Encode the rewritten input
    input_embedding = ollama.embeddings(model='mxbai-embed-large', prompt=rewritten_input)["embedding"]
    # Compute cosine similarity between the input and vault embeddings
    cos_scores = torch.cosine_similarity(torch.tensor(input_embedding).unsqueeze(0), vault_embeddings)
    # Adjust top_k if it's greater than the number of available scores
    top_k = min(top_k, len(cos_scores))
    # Sort the scores and get the top-k indices
    top_indices = torch.topk(cos_scores, k=top_k)[1].tolist()
    # Get the corresponding context from the vault
    relevant_context = [vault_content[idx].strip() for idx in top_indices]
    return relevant_context

   
def ollama_chat(user_input, l_system_message, vault_embeddings, vault_content, ollama_model, conversation_history):
    conversation_history.append({"role": "user", "content": user_input})
    
    relevant_context = get_relevant_context(user_input, vault_embeddings, vault_content)
    if relevant_context:
        context_str = "\n".join(relevant_context)
        #print("Context Pulled from Documents: \n\n" + CYAN + context_str + RESET_COLOR)
        print("Context is Pulled from Documents: now Analyzing .. \n\n" + CYAN + RESET_COLOR)
    else:
        print(CYAN + "No relevant context found." + RESET_COLOR)
    
    user_input_with_context = user_input
    if relevant_context:
        user_input_with_context = user_input + "\n\nRelevant Context:\n" + context_str
    
    conversation_history[-1]["content"] = user_input_with_context
    
    messages = [
        {"role": "system", "content": l_system_message},
        *conversation_history
    ]

    #measure
    t0 = perf_counter()
    
    response = client.chat.completions.create(
        model=ollama_model,
        messages=messages,
        max_tokens=2000,
    )
    t1 = perf_counter()
    time_taken = t1 - t0
    #print("time taken(secs) = ",int(time_taken))
    
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})
    
    return response.choices[0].message.content


# Function to upload a JSON file and append to vault.txt
def upload_jsonfile(file_path):
    print("processing",file_path," ..")
    if file_path:
        with open(file_path, 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
            
            # Flatten the JSON data into a single string
            text = json.dumps(data, ensure_ascii=False)
            
            # Normalize whitespace and clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split text into chunks by sentences, respecting a maximum chunk size
            sentences = re.split(r'(?<=[.!?]) +', text)  # split on spaces following sentence-ending punctuation
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                # Check if the current sentence plus the current chunk exceeds the limit
                if len(current_chunk) + len(sentence) + 1 < 1000:  # +1 for the space
                    current_chunk += (sentence + " ").strip()
                else:
                    # When the chunk exceeds 1000 characters, store it and start a new one
                    chunks.append(current_chunk)
                    current_chunk = sentence + " "
            if current_chunk:  # Don't forget the last chunk!
                chunks.append(current_chunk)
            with open("vault.txt", "a", encoding="utf-8") as vault_file:
                for chunk in chunks:
                    # Write each chunk to its own line
                    vault_file.write(chunk.strip() + "\n")  # Two newlines to separate chunks
            #print(f"JSON file content appended to vault.txt with each chunk on a separate line.")



## MAIN ##
# Parse command-line arguments
print(NEON_GREEN + "Parsing command-line arguments..." + RESET_COLOR)
parser = argparse.ArgumentParser(description="Ollama Chat")
parser.add_argument("--model", default="llama3.1", help="Ollama model to use (default: llama3)")
args = parser.parse_args()

# Configuration for the Ollama API client
print(NEON_GREEN + "Initializing Ollama API client..." + RESET_COLOR)
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='llama3'
)

#read TR json
upload_jsonfile(process_file)
upload_jsonfile(tr_file)
##

# Load the vault content with Process & TR info !
print(NEON_GREEN + "Loading vault content..." + RESET_COLOR)
vault_content = []
if os.path.exists("vault.txt"):
    with open("vault.txt", "r", encoding='utf-8') as vault_file:
        vault_content = vault_file.readlines()

# Generate embeddings for the vault content using Ollama
print(NEON_GREEN + "Generating embeddings for the vault content..." + RESET_COLOR)
vault_embeddings = []
for content in vault_content:
    response = ollama.embeddings(model='mxbai-embed-large', prompt=content)
    vault_embeddings.append(response["embedding"])

# Convert to tensor and print embeddings
print("Converting embeddings to tensor...")
vault_embeddings_tensor = torch.tensor(vault_embeddings) 
print("Embeddings for each line in the vault:")
print(vault_embeddings_tensor)

# Conversation loop
print("Starting conversation loop...")
conversation_history = []

system_message_default = """You are a helpful assistant that is an expert at extracting the most useful information from a given text. 
If you dont know the answer, please say so. Be clear and concise."""

rfs_instructions = """ 
#1 If Issue-Id entered by user is found in JSON Object "Issues", derive the values for the following fields from it. Else stop the analysis
#1.1 'Test Phase(found)'  : lets call it 'issue-TP'
#1.2 'should have been found in (phase)' : lets call it 'issue-SHBF(P)'
#1.3 'should have been found in (type)' : lets call it 'issue-SHBF(T)'
#1.4 reason for slippage : lets call it 'issue-RFS'.

#2 Validate issue-SHBF(P): 
#2.1 get sequence value of issue-TP, say 't'. 
#2.2 get sequence value of issue-SHBF(P), say 's' 
#2.3 If integer value of 's' from #2.2 is greater than integer value of 't' from #2.1, then flag issue-SHBF(P) value as inconsistent
#2.4 proceed to next step only if result of #2.3 is flagged as consistent. Else stop the analysis here. 

#3 Validate issue-SHBF(T): 
#3.1 If issue-SHBF(T) field does not match any of 'test_types' for that phase as listed in JSON Object "development-process", then flag the issue-SHBF(T) value as inconsistent
#3.2 proceed to next step only if result of #3.1 is flagged as consistent. Else stop the analysis here. 

#4 Validate issue-RFS: 
#4.1 If value of issue-RFS does not match any of the 'reason_for_slippage' for that phase as listed in JSON Object "development-process", then flag the issue-RFS value as inconsistent 

"""


while True:

    # input() method waits for user to input !
    user_input = input(YELLOW + "Ask a question OR Enter 1. for Issueid (or type 'quit' to exit): " + RESET_COLOR)
    if user_input.lower() == 'q' or user_input.lower() == 'quit':
        break

    # Issue-mode
    if user_input.lower() == '1':
        print("Retrieving issues for which info is available .. \n\n" + CYAN + RESET_COLOR)
        response = ollama_chat("list the issue ids you see in JSON Object Issues ", system_message_default, vault_embeddings_tensor, vault_content, args.model, conversation_history)        
        print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)

        while True: 
            user_input = input(YELLOW + "Enter the Issue-Id to analyze: " + RESET_COLOR)

            # user-entered input now in user_input var !
            if user_input.lower() == 'q' or user_input.lower() == 'quit':
                break
            user_tr_prompt = "Analyze the issue Id " + user_input + rfs_instructions         
        
            response = ollama_chat(user_tr_prompt, system_message_default, vault_embeddings_tensor, vault_content, args.model, conversation_history)
            print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)
    else:    
        #general question
        response = ollama_chat(user_input, system_message_default, vault_embeddings_tensor, vault_content, args.model, conversation_history)
        print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)
