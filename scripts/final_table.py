#!/usr/bin/env python
'''This script takes 2 input csv files generated by xtail_normalized_counts.R,
(one for uORFs and one for CDS) and creates a new data frame containing information
on regulatory uORFs and their associated mainORF.
'''

import pandas as pd
import re
import argparse
import numpy as np
import os
import math

def set_change_symbol(log2change):
    if log2change > 1:
        return "+"
    else:
        return "-"

def uORF_change(uORFrowIn,ORFreadsIn):
    #uORFString = "uORFrow" + "\t" + '\t'.join(map(str,uORFrowIn)) + "\n"
    #orfString = "ORFreads" + "\t" + '\t'.join(map(str,ORFreadsIn)) + "\n"
    uORFrow = uORFrowIn #[1:]
    ORFreads = ORFreadsIn
    replicates = math.ceil(len(uORFrow)/2)
    logchanges = []
    changesum = 0
    for replicate in range(0,replicates):
        uORFCond1 = uORFrow[replicate] + 1
        orfCond1 = ORFreads[replicate] + 1
        uORFCond2 = uORFrow[replicate + replicates] + 1
        orfCond2 = ORFreads[replicate + replicates] + 1
        ratio1 = orfCond1 / uORFCond1
        ratio2 = orfCond2  / uORFCond2 #(WT, ref)
        change =  ratio1 / ratio2
        log2change = math.log2(change)
        #logchanges.append(ratio1)
        #logchanges.append(ratio2)
        #logchanges.append(change)
        #logchanges.append(set_change_symbol(log2change))
        changesum += change
    averagechange = changesum / replicates
    #changeString = "Change" + "\t" + '\t'.join(map(str,logchanges))
    #paramsString = uORFString + orfString + changeString
    #print(paramsString)
    return (averagechange)

def uORF_changes(uorf_table,uorf_reads_dict,orf_reads_dict):
    changes = []
    #parameters = []
    for _ , uORFrow in uorf_table.iterrows():
       uORFid = uORFrow['uORF_id']
       #ORFid = re.sub(r'.\d+$', '', uORFid)
       ORFid = uORFrow['transcript_id']
       uORFreads = uorf_reads_dict[uORFid]
       ORFreads = orf_reads_dict[ORFid]
       averagechange = uORF_change(uORFreads,ORFreads)
       joined_row = '\t'.join(map(str,uORFrow))
       uORF_changes_string = joined_row + "\t" + str(averagechange) + "\t" + set_change_symbol(averagechange)
       changes.append(uORF_changes_string)
       #parameters.append(change_parameters)
    return (changes)

# read in xtail output files
def create_table(name):
    df = pd.read_table(name, sep = ",", index_col = 0)
    df = df[["log2FC_TE_final", "pvalue_final", "pvalue.adjust"]]
    return df

# extract transcript ids form uORF ids
def ids(uORFs):
	ids = []
	for i in uORFs.index.values:
		short = re.findall('(.*\.[0-9]*)\.', i)
		ids.append(short[0])
	uORFs['transcript_id'] = ids
	return uORFs

# merge both data frames by transcript id
def merge(uORFs, cds):
	df_merge = pd.merge(uORFs, cds, how = "left", left_on = "transcript_id", right_index = True, suffixes = ("_uORF", "_CDS") )
	df_merge.reset_index(level=0, inplace=True)
	df_merge.rename(columns = {"index":"uORF_id"}, inplace = True)
	return df_merge

# determine "direction of regulation"
def label(row):
	if row["log2FC_TE_final_uORF"] < 0 and row["log2FC_TE_final_CDS"] < 0: return("-,-")
	elif row["log2FC_TE_final_uORF"] > 0 and row["log2FC_TE_final_CDS"] > 0: return("+,+")
	elif row["log2FC_TE_final_uORF"] > 0 and row["log2FC_TE_final_CDS"] < 0: return("+,-")
	elif row["log2FC_TE_final_uORF"] < 0 and row["log2FC_TE_final_CDS"] > 0: return("-,+")
	else:
		return(None)

# create output data frame
def create_output(args):
	cds = create_table(args.xtail_cds_file)
	uORFs = create_table(args.xtail_uORF_file)
	uORFs = ids(uORFs)
	df_merge = merge(uORFs, cds)
	df_merge["direction"] = df_merge.apply(lambda row: label(row), axis = 1)
	annot = pd.read_table(args.uORF_annotation, sep =",", index_col = 0)
	annot.drop(columns = ["chromosome", "start", "stop", "strand", "gene_id", "strand" , "start_codon", "ORF_length", "transcript_id"], axis = 1, inplace = True)
	df_merge = pd.merge(df_merge, annot, how = "left", left_on = "uORF_id", right_on = "uORFids")
	df_merge.drop(columns = ["uORFids"], axis = 1, inplace = True)
	return(df_merge)

def main():
    # store commandline args
    parser = argparse.ArgumentParser(description='Merges xtail differential analysis of translation efficiency of uORFs and their associated mainORF.')
    parser.add_argument('--xtail_cds_file', metavar='xtail_TE', help='Path to csv file generated by xtail_normalized_counts.R on CDS')
    parser.add_argument('--xtail_uORF_file', metavar='xtail_TE', help='Path to csv file generated by xtail_normalized_counts.R on uORFs')
    parser.add_argument("--uORF_reads", help='Path to input file with uORF reads')
    parser.add_argument("--ORF_reads", help='Path to input file with ORF reads')
    parser.add_argument("--uORF_annotation", help='Path to csv file containing uORF annotation')
    parser.add_argument("--output_csv_filepath", help='Path to write merged csv output')
    args = parser.parse_args()
    uorf_reads = pd.read_csv(args.uORF_reads)
    uorf_reads = uorf_reads[uorf_reads.columns.drop(list(df.filter(regex='RNA')))]
    uorf_cols = uorf_reads.columns.values
    uORF_cols[0] = 'ID'
    uorf_reads.columns = uorf_cols
    uorf_reads_dict = uorf_reads.set_index('ID').T.to_dict('list')
    orf_reads = pd.read_csv(args.ORF_reads)
    orf_cols = orf_reads.columns.values
    orf_cols[0] = 'ID'
    orf_reads.columns = orf_cols
    orf_reads_dict = orf_reads.set_index('ID').T.to_dict('list')
    df_final = create_output(args)
    changes_list = uORF_changes(df_final,uorf_reads_dict,orf_reads_dict)
    changes_string = '\n'.join(map(str,changes_list))
    f = open(args.changes_output, 'wt', encoding='utf-8')
    f.write(changes_string)
    #df_final.to_csv(args.output_csv_filepath, index = False, na_rep = 'NA', sep = "\t")

if __name__ == '__main__':
    main()
