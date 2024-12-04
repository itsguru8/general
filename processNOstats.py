import sys
import os
import re
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 

import numpy as np
from datetime import datetime
import pandas
import csv

## check before running

#1. the xlsx sheet name containing 'raw stats' & input file name should match
#2. the xlsx files should be closed when running the script

## Input:
## 1.  atleast one of ASU/ZTI/NHC/IL raw stats file
## 2. disable flags if not processing

#E.g: python 'C:\Users\xgurpat\OneDrive - Ericsson\SHMonly\processNOstats.py' .\ASU_STATS_2024_WK45-WK46.xlsx .\AP_ZT_Usage_19_Nov.xlsm .\NHC_STATS_2024_WK45-WK46.xlsx .\SHM_STATS_2024_WK45-WK46.xlsx

if (len(sys.argv) < 2) :
    print("INPUTS: <raw_stats_file> ")
    exit()

ASU_file = sys.argv[1]
ZTI_file = sys.argv[2]
NHC_file = sys.argv[3]
SHM_file = sys.argv[4]
print("INPUT: asu_raw_stats_file: ",ASU_file)
print("INPUT: zti_raw_stats_file: ",ZTI_file)
print("INPUT: nhc_raw_stats_file: ",NHC_file)
print("INPUT: shm_raw_stats_file: ",SHM_file)


#vars
#asu
asu_opr_stats = {}
asu_ma_stats = {}
total_asu_nodes = 0


#zti
zti_opr_stats = {}
total_zti_nodes = 0

#nhc
nhc_opr_stats = {}
nhc_ma_stats = {}
total_nhc_nodes = 0

#IL
il_opr_stats = {}
il_ma_stats = {}
total_il_nodes = 0
total_il_jobs = 0
total_capEx_jobs = 0
total_upg_jobs = 0
total_int_jobs=0

now = datetime.now()
datetime_str = now.strftime("%d-%m-%Y_%H-%M-%S")

#Output
#print out
outcontent={}
outFilePath = "RANO_summary" + ".json"
#Out_pdffile = sys.argv[3]+"_"+datetime_str+".pdf"
outcontent['inputs'] = {}
outcontent['inputs']['asu_raw_stats_file'] = ASU_file
outcontent['inputs']['zti_raw_stats_file'] = ZTI_file
outcontent['inputs']['nhc_raw_stats_file'] = NHC_file
outcontent['inputs']['shm_raw_stats_file'] = SHM_file
outcontent['inputs']['time_of_processing'] = datetime_str

outcontent['stats'] = {}

## MAIN ##
conf_obj = {}
conf_obj['parse_asu_stats'] = 1
conf_obj['parse_zti_stats'] = 1
conf_obj['parse_nhc_stats'] = 1
conf_obj['parse_il_stats'] = 1

"""
# read-config obj 
conf_NOstats_file_path ="conf_NOstats.json"
with open(conf_NOstats_file_path, 'r', encoding="utf-8") as conf_file:
    conf_obj = json.load(conf_file)
print("READ: config file contents: ", conf_obj)
"""

if conf_obj['parse_asu_stats']:
    #extract needed columns
    asu_basef = os.path.basename(ASU_file)
    asu_basen = ''.join(asu_basef.split('.')[0]) # sheetname: get file name without extesion
    if "xlsx" in ASU_file:
        excel_data_df = pandas.read_excel(ASU_file, sheet_name=asu_basen,usecols=['Market Area','Operator','Node Count'])
        asu_basen += "_.csv"
        excel_data_df.to_csv(asu_basen, index=False,mode='w+')
    else :
        if not "csv" in ASU_file:
            print("ERR: input ASU file is not valid raw stats file of ext: xlsx/csv  ")
            exit()
        else:
            csv_data_df = pandas.read_csv(ASU_file, usecols=['Market Area','Operator','Node Count'])      # no need to mention sheet name  
            asu_basen += "_.csv"
            csv_data_df.to_csv(asu_basen, index=False,mode='w+')

    #post-sheet extraction, use it as input ASU file  
    ASU_file = asu_basen

    # now parse ASU csv
    with open(ASU_file) as asu_File:
        asu_lines = asu_File.readlines()
        #remove header
        asu_lines.pop(0)
        for line in asu_lines:
            line = line.strip('\n')
            asu_ma = ''.join(line.split(',')[0])
            asu_opr = ''.join(line.split(',')[1])
            asu_node_count = int(float(line.split(',')[2]))

            if asu_opr and asu_ma and asu_node_count:   # null check
                total_asu_nodes += asu_node_count
                if not asu_opr_stats.get(asu_opr):
                    asu_opr_stats[asu_opr] = 0
                #opr-level
                asu_opr_stats[asu_opr] += asu_node_count
                #ma-level
                if not asu_ma_stats.get(asu_ma):
                    asu_ma_stats[asu_ma] = 0
                asu_ma_stats[asu_ma] += asu_node_count
            else:
                print("discarding line: ",line)
    
    outcontent['stats']['total_asu_nodes'] = total_asu_nodes
    outcontent['stats']['total_asu_opr'] = len(asu_opr_stats)
    sorted_asu_opr_stats = dict(sorted(asu_opr_stats.items(), key=lambda item:item[1], reverse=True))    
    sorted_asu_ma_stats = dict(sorted(asu_ma_stats.items(), key=lambda item:item[1], reverse=True))    
    outcontent['asu'] = {}
    outcontent['asu']['ma_stats'] = sorted_asu_ma_stats
    outcontent['asu']['opr_stats'] = sorted_asu_opr_stats


if conf_obj['parse_zti_stats']:

    if "xlsm" in ZTI_file:
        file_no_ext = os.path.basename(ZTI_file)
        file_no_ext = ''.join(file_no_ext.split('.')[0]) # get file name without extesion
        excel_data_df1 = pandas.read_excel(ZTI_file, sheet_name='ZTCommand')
        file_no_ext += "_.csv"
        excel_data_df1.to_csv(file_no_ext, index=False,mode='w+')
        #overwrite input file name
        ZTI_file = file_no_ext
        #print("ZTI raw stats file: ",analysis_1_file)
    else :
        print("ERR: input file #1 is not valid raw stats file of ext: xlsm  ")
        exit()

    #time	site	projectName	nodeName
    f1_ZTI_opr_node_count = {}
    with open(ZTI_file, "r") as raw_1_stats:
        lines = raw_1_stats.readlines()
        #remove header
        lines.pop(0)

        for line in lines:
            site = ''.join(line.split(',')[1]) # Airtel_Libreville_ltcenm01lms,
            l_opr = ''.join(site.split('_')[0])

            if l_opr :
                if not zti_opr_stats.get(l_opr):
                    zti_opr_stats[l_opr] = 0 # create key 1st time
                zti_opr_stats[l_opr] += 1
                total_zti_nodes += 1
            
    outcontent['stats']['total_zti_nodes'] = total_zti_nodes
    outcontent['stats']['total_zti_opr'] = len(zti_opr_stats)
    sorted_zti_opr_stats = dict(sorted(zti_opr_stats.items(), key=lambda item:item[1], reverse=True))    
    outcontent['zti'] = {}
    outcontent['zti']['opr_stats'] = sorted_zti_opr_stats


if conf_obj['parse_nhc_stats']:
    #extract needed columns
    nhc_basef = os.path.basename(NHC_file)
    nhc_basen = ''.join(nhc_basef.split('.')[0]) # sheetname: get file name without extesion
    if "xlsx" in NHC_file:
        excel_data_df = pandas.read_excel(NHC_file, sheet_name=nhc_basen,usecols=['Market Area','Operator','NodeCount'])
        nhc_basen += "_.csv"
        excel_data_df.to_csv(nhc_basen, index=False,mode='w+')
    else :
        if not "csv" in NHC_file:
            print("ERR: input NHC file is not valid raw stats file of ext: xlsx/csv  ")
            exit()
        else:
            csv_data_df = pandas.read_csv(NHC_file, usecols=['Market Area','Operator','NodeCount'])      # no need to mention sheet name  
            nhc_basen += "_.csv"
            csv_data_df.to_csv(nhc_basen, index=False,mode='w+')

    #post-sheet extraction, use it as input NHC file  
    NHC_file = nhc_basen

    # now parse NHC csv
    with open(NHC_file) as nhc_File:
        nhc_lines = nhc_File.readlines()
        #remove header
        nhc_lines.pop(0)
        for line in nhc_lines:
            line = line.strip('\n')
            #print(line)
            nhc_ma = ''.join(line.split(',')[0])
            nhc_opr = ''.join(line.split(',')[1])
            nhc_node_count = int(float(line.split(',')[2]))

            if nhc_opr and nhc_ma and nhc_node_count:   # null check
                total_nhc_nodes += nhc_node_count
                if not nhc_opr_stats.get(nhc_opr):
                    nhc_opr_stats[nhc_opr] = 0
                #opr-level
                nhc_opr_stats[nhc_opr] += nhc_node_count
                #ma-level
                if not nhc_ma_stats.get(nhc_ma):
                    nhc_ma_stats[nhc_ma] = 0
                nhc_ma_stats[nhc_ma] += nhc_node_count
            else:
                print("discarding line: ",line)
    
    outcontent['stats']['total_nhc_nodes'] = total_nhc_nodes
    outcontent['stats']['total_nhc_opr'] = len(nhc_opr_stats)
    sorted_nhc_opr_stats = dict(sorted(nhc_opr_stats.items(), key=lambda item:item[1], reverse=True))    
    sorted_nhc_ma_stats = dict(sorted(nhc_ma_stats.items(), key=lambda item:item[1], reverse=True))    
    outcontent['nhc'] = {}
    outcontent['nhc']['ma_stats'] = sorted_nhc_ma_stats
    outcontent['nhc']['opr_stats'] = sorted_nhc_opr_stats


if conf_obj['parse_il_stats']:

    shm_basef = os.path.basename(SHM_file)
    shm_basen = ''.join(shm_basef.split('.')[0]) # get file name without extesion

    #extract needed columns
    if "xlsx" in SHM_file:
        excel_data_df2 = pandas.read_excel(SHM_file, sheet_name=shm_basen,usecols=['Market Area','Operator','JobType','NodeCount','JobName'])
        shm_basen += "_.csv"
        excel_data_df2.to_csv(shm_basen, index=False,mode='w+')
    else :
        if not "csv" in SHM_file:
            print("ERR: input SHM file is not valid raw stats file of ext: xlsx/csv  ")
            exit()
        else:
            csv_data_df2 = pandas.read_csv(SHM_file, usecols=['Market Area','Operator','JobType','NodeCount','JobName'])        
            shm_basen += "_.csv"
            csv_data_df2.to_csv(shm_basen, index=False,mode='w+')

    #overwrite input SHM file name
    SHM_file = shm_basen

    # now parse SHM csv
    with open(SHM_file, "r") as SHM_raw_stats:
        lines = SHM_raw_stats.readlines()
        #remove header
        lines.pop(0)

        for line in lines:
            line = line.strip('\n')
            shm_job_type = ''.join(line.split(',')[2])

            if "LICENSE_REQUEST" not in shm_job_type :
                continue

            #print(line)
            l_ma = ''.join(line.split(',')[0]) # market area
            shm_opr = ''.join(line.split(',')[1]) # "opr" name e.g. STC-SA, Zain-BH
            il_node_count = int(float(line.split(',')[3])) # node count

            if not l_ma or not shm_opr or not il_node_count :
                print("discarding line: ",line)
                continue

            total_il_nodes += il_node_count
            total_il_jobs += 1
            #opr-level
            if not il_opr_stats.get(shm_opr):
                il_opr_stats[shm_opr] = 0
            il_opr_stats[shm_opr] += il_node_count

            #ma-level
            if not il_ma_stats.get(l_ma):
                il_ma_stats[l_ma] = 0
            il_ma_stats[l_ma] += il_node_count

            #job stats
            il_job_name = ''.join(line.split(',')[4])
            if "CapacityExpansionLicense" in il_job_name :
                 total_capEx_jobs += 1
            elif "UpgradeLicense" in il_job_name or "RefreshLicense" in il_job_name :
                total_upg_jobs += 1
            elif  "IntegrationLicense" in il_job_name :
                total_int_jobs += 1
            else :
                # do nothing
                continue

    outcontent['stats']['total_il_nodes'] = total_il_nodes
    outcontent['stats']['total_il_opr'] = len(il_opr_stats)
    sorted_il_opr_stats = dict(sorted(il_opr_stats.items(), key=lambda item:item[1], reverse=True))    
    sorted_il_ma_stats = dict(sorted(il_ma_stats.items(), key=lambda item:item[1], reverse=True))    
    outcontent['il'] = {}
    outcontent['il']['ma_stats'] = sorted_il_ma_stats
    outcontent['il']['opr_stats'] = sorted_il_opr_stats
    outcontent['il']['opr_stats'] = sorted_il_opr_stats
    outcontent['il']['jobs'] = {}
    outcontent['il']['jobs']['total_il_jobs'] = total_il_jobs
    outcontent['il']['jobs']['total_capEx_jobs'] = total_capEx_jobs
    outcontent['il']['jobs']['total_refresh_jobs'] = total_upg_jobs
    outcontent['il']['jobs']['total_int_jobs'] = total_int_jobs

##
# dump this info

with open(outFilePath, "w+") as outfile:
    json.dump(outcontent, outfile)
    print("[READY]see results file(s): ",outFilePath)







