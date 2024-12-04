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

#simple chat
def ollama_simple_chat(user_input, l_system_message, ollama_model, conversation_history):

    conversation_history.append({"role": "user", "content": user_input})
    conversation_history[-1]["content"] = user_input
    messages = [
        {"role": "system", "content": l_system_message},
        *conversation_history
    ]

    t0 = perf_counter()
    #print("##request: ", messages)

    response = client.chat.completions.create(
        model=ollama_model,
        messages=messages,
        max_tokens=2000,
    )
    t1 = perf_counter()
    time_taken = t1 - t0
    print("time taken(secs) = ",int(time_taken))
    
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})
    return response.choices[0].message.content


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

# Conversation loop
print("Starting conversation loop...")
conversation_history = []

system_message_default = """You are a helpful assistant that is an expert at extracting the most useful information from a given text. 
If you dont know the answer, please say so. Be clear and concise."""

while True:

    # input() method waits for user to input !
    user_input = input(YELLOW + "Ask a question (or type 'quit' to exit): " + RESET_COLOR)
    if user_input.lower() == 'q' or user_input.lower() == 'quit':
        break

    response = ollama_simple_chat(user_input, system_message_default, args.model, conversation_history)
    print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)
