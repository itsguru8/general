import sys
import os
import re
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 

import numpy as np
from datetime import datetime
import pandas as pd

## Input:
## 1. SHM-only-usage-analysis#1
## 2. SHM-only-usage-analysis#2
if (len(sys.argv) < 4) :
    print("INPUTS: ZTI-rawStats#1 ZTI-rawStats#2 Analysis_title")
    exit()

print("INPUT: analysis#1: ",sys.argv[1])
print("INPUT: analysis#2: ",sys.argv[2])
print("INPUT: analysis#Title: ",sys.argv[3])


#AP_ZT_Usage_08_Oct_rawStats
analysis_1_file = sys.argv[1]

#AP_ZT_Usage_31_Dec_2023_rawStats
analysis_2_file = sys.argv[2]

analysis_title = sys.argv[3]

now = datetime.now()
datetime_str = now.strftime("%d-%m-%Y_%H-%M-%S")

#Output
#print out
outcontent={}
outFilePath="compare_ZTI-Opr.json"
Out_pdffile = "compare_ZTI-Usage"

  
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


# UT
input_parse = 1

if input_parse :

    if "xlsm" in analysis_1_file:
        ap_basef = os.path.basename(analysis_1_file)
        file_no_ext = ''.join(ap_basef.split('.')[0]) # get file name without extesion
        file_no_ext += "_.csv"
        excel_data_df1 = pd.read_excel(analysis_1_file, sheet_name='ZTCommand',usecols=['site'])
        excel_data_df1.to_csv(file_no_ext, index=False,mode='w+')
        #overwrite input file name
        analysis_1_file = file_no_ext
        #print("ZTI raw stats file: ",analysis_1_file)
    else :
        if not "csv" in analysis_1_file:
            print("ERR: input file #1 is not valid raw stats file of ext: xlsm/csv  ")
            exit()


    if "xlsm" in analysis_2_file:
        ap_basef = os.path.basename(analysis_2_file)
        file2_no_ext = ''.join(ap_basef.split('.')[0]) # get file name without extesion
        file2_no_ext += "_.csv"
        excel_data_df2 = pd.read_excel(analysis_2_file, sheet_name='ZTCommand',usecols=['site'])
        excel_data_df2.to_csv(file2_no_ext, index=False,mode='w+')
        #overwrite input file name
        analysis_2_file = file2_no_ext
    else :
        if not "csv" in analysis_2_file:
            print("ERR: input file #2 is not valid raw stats file of ext: xlsm/csv  ")
            exit()

# AT this point , both csv are ready in local dir !!

analysis_1_stats = {}
analysis_2_stats = {}

#Row Labels,Count of nodeName
#Airtel_Libreville_ltcenm01lms,11
f1_ZTI_opr_node_count = {}
with open(analysis_1_file, "r") as raw_1_stats:
    lines = raw_1_stats.readlines()
    #remove header
    #time	site	projectName	nodeName	neType
    lines.pop(0)

    for site in lines:
        l_opr = ''.join(site.split('_')[0])
        if not f1_ZTI_opr_node_count.get(l_opr):
            f1_ZTI_opr_node_count[l_opr] = 0 # create key 1st time
        f1_ZTI_opr_node_count[l_opr] += 1

#stats
#print("ZTI stats: ",f1_ZTI_opr_node_count)


#Row Labels,Count of nodeName
#Airtel_Libreville_ltcenm01lms,11
f2_ZTI_opr_node_count = {}
with open(analysis_2_file, "r") as raw_2_stats:
    lines = raw_2_stats.readlines()
    #remove header
    #time	site	projectName	nodeName	neType
    lines.pop(0)

    for site in lines:
        l_opr = ''.join(site.split('_')[0])
        if not f2_ZTI_opr_node_count.get(l_opr):
            f2_ZTI_opr_node_count[l_opr] = 0 # create key 1st time
        f2_ZTI_opr_node_count[l_opr] += 1

# now compare f1 & f2 results

unique_1_list = {}
common_1_list = {}
unique_2_list = {}

for i in f1_ZTI_opr_node_count.keys():
    if  f2_ZTI_opr_node_count.get(i):
        common_1_list[i] = f1_ZTI_opr_node_count[i]
    else:
        unique_1_list[i] = f1_ZTI_opr_node_count[i]

for j in f2_ZTI_opr_node_count.keys():
    if  not common_1_list.get(j):
        unique_2_list[j] = f2_ZTI_opr_node_count[j]


#dump this info
outcontent['inputs'] = {}
outcontent['inputs']['file_1'] = analysis_1_file
outcontent['inputs']['file_2'] = analysis_2_file
outcontent['inputs']['time_of_processing'] = datetime_str

outcontent['comparison'] = {}

Total_ZTI_file_1_Opr = analysis_1_file
Total_ZTI_file_2_Opr = analysis_2_file

outcontent['comparison']['stats'] = {}
outcontent['comparison']['stats'][Total_ZTI_file_1_Opr] = len(f1_ZTI_opr_node_count.keys())
outcontent['comparison']['stats'][Total_ZTI_file_2_Opr] = len(f2_ZTI_opr_node_count.keys())
outcontent['comparison']['stats']['ZTI_continue'] = len(common_1_list)
outcontent['comparison']['stats']['ZTI++'] = len(unique_1_list)
outcontent['comparison']['stats']['ZTI--'] = len(unique_2_list)

sorted_add_stats = dict(sorted(unique_1_list.items(), key=lambda item:item[1], reverse=True)) 
sorted_drop_stats = dict(sorted(unique_2_list.items(), key=lambda item:item[1], reverse=True))
sorted_cont_stats = dict(sorted(common_1_list.items(), key=lambda item:item[1], reverse=True))

add_tag = "ZTI++ (" + analysis_1_file + ")"
outcontent['comparison'][add_tag] = sorted_add_stats
drop_tag = "ZTI-- (" + analysis_2_file + ")"
outcontent['comparison'][drop_tag] = sorted_drop_stats
comm_tag = "ZTI common (" + analysis_1_file + ")"
outcontent['comparison'][comm_tag] = sorted_cont_stats

##
#write output
##

with open(outFilePath, "w+") as outfile:
    json.dump(outcontent, outfile)
    print("[READY]see Compare results file(s): ",outFilePath)


##
#PLOTS
o_plot_names = np.array(list(outcontent['comparison']['stats'].keys()))
o_plot_names = np.char.replace(o_plot_names,"-","\n")
     
o_plot_values = np.array(list(outcontent['comparison']['stats'].values()))
plt.bar(o_plot_names, o_plot_values)
for i in range(len(o_plot_names)):
    plt.text(i, o_plot_values[i], o_plot_values[i], ha = 'center', fontsize = 6)

plt.title(analysis_title)
plt.xlabel("stats")
plt.ylabel("values")
plt.figure()

drop_plot = 1

if drop_plot :

    # ZTI add
    column_labels=["ZTI++: Opr"]

    fig, ax =plt.subplots(1,1)
    add_title = "ZTI new Opr stats (" + analysis_1_file + ")"
    ax.set_title(add_title, fontsize=16,loc='left')

    plt.subplots_adjust(top=0.8)

    df=pd.DataFrame(list(sorted_add_stats.values()),columns=column_labels)
    #print("sorted drop stats: ",sorted_drop_stats)

    ax.axis('tight') #turns off the axis lines and labels
    ax.axis('off') #changes x and y axis limits such that all data is shown

    #plotting data
    table = ax.table(cellText=df.values,
            colLabels=df.columns,
            rowLabels=list(sorted_add_stats.keys()),
            loc="center")
    table.set_fontsize(6)
    #table.auto_set_font_size()
    table.auto_set_column_width(1)

#####################
    # ZTI drop
    column_labels=["ZTI--: Opr"]

    fig2, ax2 =plt.subplots(1,1)
    drop_title = "ZTI drop Opr stats (" + analysis_2_file + ")"
    ax2.set_title(drop_title, fontsize=16,loc='left')

    plt.subplots_adjust(top=0.8)

    df2=pd.DataFrame(list(sorted_drop_stats.values()),columns=column_labels)
    #print("sorted drop stats: ",sorted_drop_stats)

    ax2.axis('tight') #turns off the axis lines and labels
    ax2.axis('off') #changes x and y axis limits such that all data is shown

    #plotting data
    table2 = ax2.table(cellText=df2.values,
            colLabels=df2.columns,
            rowLabels=list(sorted_drop_stats.keys()),
            loc="center")
    table2.set_fontsize(6)
    #table.auto_set_font_size()
    table2.auto_set_column_width(1)

####### continue
comm_plot = 0

if comm_plot :

    column_labels=["ZTI continue: Opr"]

    fig3, ax3 =plt.subplots(1,1)
    cont_title = "ZTI continue Opr stats (" + analysis_1_file + ")"
    ax3.set_title(cont_title, fontsize=16,loc='left')

    plt.subplots_adjust(top=0.5)

    df3=pd.DataFrame(list(sorted_cont_stats.values()),columns=column_labels)
    #print("sorted drop stats: ",sorted_drop_stats)

    ax3.axis('tight') #turns off the axis lines and labels
    ax3.axis('off') #changes x and y axis limits such that all data is shown

    #plotting data
    table3 = ax3.table(cellText=df3.values,
            colLabels=df3.columns,
            rowLabels=list(sorted_cont_stats.keys()),
            loc="center")
    table3.set_fontsize(4)
    #table.auto_set_font_size()
    #table3.auto_set_column_width(1)




## PLOTS-END




#finally write everything to pdf file
Out_pdffile += datetime_str+".pdf"

save_image(Out_pdffile)
print("[READY]see plots file(s): ",Out_pdffile)









