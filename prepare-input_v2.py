import os
#import argparse
import re
import json
import sys

if (len(sys.argv) < 3) :
    print("INPUTS: <input_tr_file> <curated_out_file> ")
    exit()

#file_path = "pilotTRsDump.json"
file_path = sys.argv[1]
#inputfile_for_localAI = "input_for_localAI.json"
inputfile_for_localAI = sys.argv[2]

#field ref
"""
"Issue-id": "key",
"summary":"['fields']['summary']",
"Issue Description" : "['fields']['customfield_25119']",
"Impact": "['fields']['customfield_30068']",
"Resolution Details" : "['fields']['customfield_39227']"
Test phase (.val): 19973
SHBF(P) (.val): 48911
SHBF(T)(.val): 48912
Reason for slippage (.val): 48913
] 
"""


#inputfile_for_localAI = "input_for_localAI.json"
ericsson_terms_file = 'prop-terms-remove_v2.json'
final_json_out = []
final_json_key_val = {}

#Read all E// repl info
erc_data = {}
with open(ericsson_terms_file, 'r') as erc_file:
  erc_data = json.load(erc_file)

if not file_path:
  print("invalid file: ",file_path)
  exit()

with open(file_path, 'r', encoding="utf-8") as json_file:
  data = json.load(json_file)

  for i in data['issues']:

    if not i['key']:
      print ("invalid key, continuing ..")
      continue

    print("processing : ",i['key'],"..")
    #refresh the vars
    outjson = {}
    content = {}

    ### REMOVE E// data before write !! 
    for j in erc_data.keys():

      #Replace in all fields
      #print("looking for : ",j," to replace with: ",erc_data[j])
      compileObj = re.compile(re.escape(j), re.IGNORECASE)

      i['key'] = compileObj.sub(erc_data[j], i['key'])

      if i['fields']['summary'] :
          i['fields']['summary'] = compileObj.sub(erc_data[j], i['fields']['summary'])

      if i['fields']['customfield_25119'] :
          i['fields']['customfield_25119'] = compileObj.sub(erc_data[j], i['fields']['customfield_25119'])

      if i['fields']['customfield_30068'] :
          i['fields']['customfield_30068'] = compileObj.sub(erc_data[j], i['fields']['customfield_30068'])

      if i['fields']['customfield_39227']: 
          i['fields']['customfield_39227'] = compileObj.sub(erc_data[j], i['fields']['customfield_39227'])

      if i['fields']['customfield_19973'] :
        if i['fields']['customfield_19973']['value'] :
          i['fields']['customfield_19973']['value'] = compileObj.sub(erc_data[j], i['fields']['customfield_19973']['value'])

      if i['fields']['customfield_48911'] :
        if i['fields']['customfield_48911']['value'] :
          i['fields']['customfield_48911']['value'] = compileObj.sub(erc_data[j], i['fields']['customfield_48911']['value'])

      if i['fields']['customfield_48912'] :
        if i['fields']['customfield_48912']['value'] :
          i['fields']['customfield_48912']['value'] = compileObj.sub(erc_data[j], i['fields']['customfield_48912']['value'])

      if i['fields']['customfield_48913'] :
        if i['fields']['customfield_48913']['value'] :
          i['fields']['customfield_48913']['value'] = compileObj.sub(erc_data[j], i['fields']['customfield_48913']['value'])

      if i['fields']['summary']:
        content['summary'] = i['fields']['summary']

      """
      if i['fields']['customfield_25119']:  #Issue desc
        content['Issue Description'] = i['fields']['customfield_25119']

      if i['fields']['customfield_30068']: #Impact
        content['Impact'] = i['fields']['customfield_30068']

      if i['fields']['customfield_39227']: #Resolution details
        content['Resolution Details'] = i['fields']['customfield_39227']
      """

      if i['fields']['customfield_19973']: # Test phase
        if i['fields']['customfield_19973']['value']:
          content['Test Phase(found)'] = i['fields']['customfield_19973']['value']

      if i['fields']['customfield_48911']: #SHBF(P)
        if i['fields']['customfield_48911']['value']:
          content['Should have been found in (phase)'] = i['fields']['customfield_48911']['value']

      if i['fields']['customfield_48912']: #SHBF(T)
        if i['fields']['customfield_48912']['value']:
          content['Should have been found in (type)'] = i['fields']['customfield_48912']['value']

      if i['fields']['customfield_48913']: #RFS
        if i['fields']['customfield_48913']['value']:
          content['Reason for slippage'] = i['fields']['customfield_48913']['value']

    #for erc keys
    outjson['Issue-Id'] = i['key']
    outjson['fields'] = content
    final_json_out.append(outjson)
    print("wrote key ="+outjson['Issue-Id'])
  #for-end

  final_json_key_val['Issues'] = final_json_out
  
  with open(inputfile_for_localAI, "w+") as outfile:
    json.dump(final_json_key_val, outfile)

  print ("see file :"+inputfile_for_localAI)


