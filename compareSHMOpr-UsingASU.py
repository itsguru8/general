import sys
import os
import re
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 
#import matplotlib.image as Image
from PIL import Image

import numpy as np
from datetime import datetime
import pandas as pd

## Input:
## 1. SHM-only-usage-analysis#1
## 2. SHM-only-usage-analysis#2
if (len(sys.argv) < 4) :
    print("INPUTS: ASU_SHM-usage-analysis#1 ASU_SHM-usage-analysis#2 Analysis_title")
    exit()

print("INPUT: analysis#1: ",sys.argv[1])
print("INPUT: analysis#2: ",sys.argv[2])
print("INPUT: analysis#Title: ",sys.argv[3])

## check before running

#1. pass the recent file first (e.g. 2024 )against which (e.g 2023) the compare is needed. 
#2. TODO: try include the figure in pdf

## Operator config file:
## ma-operator mapping file
## 
conf_file = "conf_asu_analyze.json"
conf_param = {}

# read-config obj 
with open(conf_file, 'r', encoding="utf-8") as json_conf_file:
    conf_param = json.load(json_conf_file)
print("Config param: ", conf_param)

# asu+shm analysis/2024 : 
analysis_1_file = sys.argv[1]
file1_base = os.path.basename(analysis_1_file)
file1_name = ''.join(file1_base.split('.')[0])

# asu+shm analysis/2023 : 
analysis_2_file = sys.argv[2]
file2_base = os.path.basename(analysis_2_file)
file2_name = ''.join(file2_base.split('.')[0])

analysis_title = sys.argv[3]

now = datetime.now()
datetime_str = now.strftime("%d-%m-%Y_%H-%M-%S")

#Output
#print out
outcontent={}
outFilePath="comparison_"+analysis_title+".json"
out_pdffile = "comparison_"+analysis_title+datetime_str+".pdf"

  
def save_image(pdffile): 
    p = PdfPages(pdffile)       
    fig_nums = plt.get_fignums()   
    figs = [plt.figure(n) for n in fig_nums] 
      
    for fig in figs:  
        fig.savefig(p, format='pdf')  
    p.close()   




####################################################################################################################
## MAIN ##
####################################################################################################################

analysis_1_stats = {}
analysis_2_stats = {}


with open(analysis_1_file, 'r', encoding="utf-8") as json_1_file:
    analysis_1_stats = json.load(json_1_file)
print("READ: ", analysis_1_file)

with open(analysis_2_file, 'r', encoding="utf-8") as json_2_file:
    analysis_2_stats = json.load(json_2_file)
print("READ: ", analysis_2_file)


# If NOT UT
if conf_param['parse_input_files'] != 0 :

    #asu-perspective 
    Total_ASU_file_1_Opr = "ASU_" + file1_name  #A-file1
    Total_ASU_file_2_Opr = "ASU_" + file2_name  #A-file2
    #Comparison is w.r.t File1
    List_ASU_opr_continue = []    
    List_ASU_opr_migrated_in = []                           # <-- no. of SL2 in AL-1   = S2A 
    #net new ASU (green-field)
    List_ASU_opr_green = []                                   # <-- not in A2 & not S2A 

    List_ASU_opr_migrated_out = []                          # <-- no. of AL2 in SL-1  = A2S


    # A2 not in A1 , yet to use
    List_ASU_opr_yellow = []

    #shm-perspective
    Total_SHM_file_1_Opr = "SHM-Only_" + file1_name
    Total_SHM_file_2_Opr = "SHM-Only_" + file2_name

    #analysis w.r.t file1

    #++++++++++++++++++++++++++
    #continue A2-> A1
    for i in analysis_2_stats["asu"]["asu_operators"].keys():
        if  analysis_1_stats["asu"]["asu_operators"].get(i):
            List_ASU_opr_continue.append(i)


    #List_ASU_opr_migrated_in = []                           # <-- no. of SL2 in AL-1   = S2A 

    for i in analysis_2_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys():
        if  analysis_1_stats["asu"]["asu_operators"].get(i):
            #print("[++]Opr: ",i," moved from SHM to ASU")
            List_ASU_opr_migrated_in.append(i)
        
    #net new ASU (green-field)
    for i in analysis_1_stats["asu"]["asu_operators"].keys():
        if not i in List_ASU_opr_continue :
            if not i in List_ASU_opr_migrated_in :   # newly migrated from SHM to ASU
                #print("[++]Opr: ",i," newly added to ASU usage")
                List_ASU_opr_green.append(i)

    #++++++++++++++++++++++++++

    #--------------------------
    #List_ASU_opr_migrated_out = []                          # <-- no. of AL2 in SL-1  = A2S
    #if username.upper() in (name.upper() for name in USERNAMES):

    for i in analysis_2_stats["asu"]["asu_operators"].keys():
        if not i in analysis_1_stats["asu"]["asu_operators"].keys():
            if i in analysis_1_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys():  # migrated out
                List_ASU_opr_migrated_out.append(i)
            else : # yet to use
                List_ASU_opr_yellow.append(i)

    #--------------------------


    ##
    #write output
    ##

    # dump this info
    outcontent['inputs'] = {}
    outcontent['inputs']['file_1'] = analysis_1_file
    outcontent['inputs']['file_2'] = analysis_2_file
    outcontent['inputs']['time_of_processing'] = datetime_str

    outcontent['comparison'] = {}

    outcontent['comparison']['stats'] = {}
    #outcontent['comparison']['stats'][Total_SHM_file_1_Opr] = len(analysis_1_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys())
    #outcontent['comparison']['stats'][Total_SHM_file_2_Opr] = len(analysis_2_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys())
    outcontent['comparison']['stats'][Total_ASU_file_1_Opr] = len(analysis_1_stats["asu"]["asu_operators"].keys())
    outcontent['comparison']['stats'][Total_ASU_file_2_Opr] = len(analysis_2_stats["asu"]["asu_operators"].keys())


    outcontent['comparison']['stats']['continue'] = len(List_ASU_opr_continue)
    outcontent['comparison']['stats']['migrated_IN++'] = len(List_ASU_opr_migrated_in)
    outcontent['comparison']['stats']['new++'] = len(List_ASU_opr_green)

    #asu drop out
    #discounting opr addition-count, IDEALLY everyone should continue ASU  , and nobody should drop !
    outcontent['comparison']['stats']['drop--'] = len(List_ASU_opr_continue) - len(analysis_2_stats["asu"]["asu_operators"].keys())

    if outcontent['comparison']['stats']['drop--'] < 0 :
        if len(List_ASU_opr_migrated_out) > 0 :
            outcontent['comparison']['stats']['to_SHM--'] = -(len(List_ASU_opr_migrated_out))
        if len(List_ASU_opr_yellow) > 0 :
            outcontent['comparison']['stats']['yet_to_use--'] = -(len(List_ASU_opr_yellow))

    outcontent['comparison']['opr_list'] = {}
    outcontent['comparison']['opr_list']['asu_continue'] = List_ASU_opr_continue
    outcontent['comparison']['opr_list']['asu_migrated_IN'] = List_ASU_opr_migrated_in
    outcontent['comparison']['opr_list']['asu_new'] = List_ASU_opr_green
    outcontent['comparison']['opr_list']['asu_migrated_to_SHM'] = List_ASU_opr_migrated_out
    outcontent['comparison']['opr_list']['asu_yet_to_use'] = List_ASU_opr_yellow

    outcontent['input_opr_list'] = {}
    outcontent['input_opr_list'][Total_ASU_file_1_Opr] = list(analysis_1_stats["asu"]["asu_operators"].keys())
    outcontent['input_opr_list'][Total_ASU_file_2_Opr] = list(analysis_2_stats["asu"]["asu_operators"].keys())
    outcontent['input_opr_list'][Total_SHM_file_1_Opr] = list(analysis_1_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys())
    outcontent['input_opr_list'][Total_SHM_file_2_Opr] = list(analysis_2_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"].keys())


    #finally dump outcontent
    with open(outFilePath, "w+") as outfile:
        json.dump(outcontent, outfile)
        print("[READY]see Compare results file(s): ",outFilePath)

else :  # NOT UT case !!
    with open(outFilePath, 'r', encoding="utf-8") as json_out_file:
        outcontent = json.load(json_out_file)
    print("READ back: ", outFilePath)


##
#PLOTS


if conf_param['plot_bkgnd'] != 0 : 
    im = Image.open('ASU-YoY-analysis.jpg')
    plt.figimage(im)
    plt.figure()

if conf_param['plot_stats'] != 0 : 
  
    o_plot_names = np.array(list(outcontent['comparison']['stats'].keys()))
    o_plot_names = np.char.replace(o_plot_names,"_","\n")
        
    o_plot_values = np.array(list(outcontent['comparison']['stats'].values()))
    plt.bar(o_plot_names, o_plot_values)
    plt.xticks(fontsize=6)

    for i in range(len(o_plot_names)):
        plt.text(i, o_plot_values[i], o_plot_values[i], ha = 'center', fontsize = 8)

    plt.title(analysis_title)
    plt.xlabel("stats")
    plt.ylabel("ASU Opr count")
    plt.figure()


### 
if conf_param['plot_support_data'] != 0 : 

    opr_drop_info = {}
    for i_opr in outcontent['comparison']['opr_list']['asu_migrated_to_SHM'] :
        shm_count = analysis_1_stats["SHM_only_Usage_analysis"]["top_operators_across_MA"][i_opr]
        asu_count = analysis_2_stats["asu"]["asu_operators"][i_opr]
        opr_drop_info[i_opr] = [shm_count,asu_count]  # this & 'column labels' in line below have to be in sync !!! 

    column_labels=["nodes in SHM-Only(2024)","nodes in ASU(2023)"]
    sorted_drop_stats = dict(sorted(opr_drop_info.items(), key=lambda item:item[1], reverse=True))    
    
    fig, ax =plt.subplots(1,1)
    ax.set_title("ASU drop stats", fontsize=16,loc='left')

    plt.subplots_adjust(top=0.8)

    df=pd.DataFrame(list(sorted_drop_stats.values()),columns=column_labels)
    #print("sorted drop stats: ",sorted_drop_stats)

    ax.axis('tight') #turns off the axis lines and labels
    ax.axis('off') #changes x and y axis limits such that all data is shown

    #plotting data
    table = ax.table(cellText=df.values,
            colLabels=df.columns,
            rowLabels=list(sorted_drop_stats.keys()),
            loc="center")
    table.set_fontsize(6)
    #table.auto_set_font_size()
    table.auto_set_column_width(1)


##


#finally write everything to pdf file

save_image(out_pdffile)
print("[READY]see plots file(s): ",out_pdffile)









