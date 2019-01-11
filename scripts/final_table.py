#!/usr/bin/env python
'''This script takes ORF annotation from merged ribotish output
and computes the ribo_change parameter for uORFs.
'''

import pandas as pd
import argparse
import math
#from scipy.stats import norm
import scipy.stats as stats
import numpy as np

def set_change_symbol(log2change):
    if log2change > 1:
        return "+"
    else:
        return "-"


def uORF_change(uORFrowIn, ORFreadsIn):
    uORFrow = uORFrowIn
    ORFreads = ORFreadsIn
    replicates = math.ceil(len(uORFrow)/2)
    uorf1sum = 0
    orf1sum = 0
    uorf2sum = 0
    orf2sum = 0
    changesum = 0
    for replicate in range(0, replicates):
        uORFCond1 = uORFrow[replicate] + 1
        orfCond1 = ORFreads[replicate] + 1
        uORFCond2 = uORFrow[replicate + replicates] + 1
        orfCond2 = ORFreads[replicate + replicates] + 1
        ratio1 = orfCond1 / uORFCond1
        ratio2 = orfCond2 / uORFCond2
        change = ratio1 / ratio2
        uorf1sum += uORFCond1
        orf1sum += orfCond1
        uorf2sum += uORFCond2
        orf2sum += orfCond2
        changesum += change
    averageuORF1 = uorf1sum / replicates 
    averageORF1 = orf1sum / replicates
    averageuORF2 = uorf2sum / replicates 
    averageORF2 = orf2sum / replicates
    averagechange = changesum / replicates
    logaveragechange = math.log2(averagechange)
    return (averagechange,averageuORF1,averageORF1,averageuORF2,averageORF2,logaveragechange)

def uORF_changes(uorf_table, uorf_reads_dict, orf_reads_dict):
    averagechanges = []
    averageuORF1s = []
    averageORF1s = []
    averageuORF2s = []
    averageORF2s = []
    logaveragechanges = []
    for _, uORFrow in uorf_table.iterrows():
        uORFid = uORFrow['uORFids']
        ORFid = uORFrow['transcript_id']
        uORFreads = uorf_reads_dict[uORFid]
        ORFreads = orf_reads_dict[ORFid]
        (averagechange,averageuORF1,averageORF1,averageuORF2,averageORF2,logaveragechange) = uORF_change(uORFreads, ORFreads)
        averageuORF1s.append(averageuORF1)
        averageORF1s.append(averageORF1)
        averageuORF2s.append(averageuORF2)
        averageORF2s.append(averageORF2)
        averagechanges.append(averagechange)
        logaveragechanges.append(logaveragechange)
    uorf_table['averageuORF1'] = averageuORF1s
    uorf_table['averageORF1'] = averageORF1s
    uorf_table['averageuORF2'] = averageuORF2s
    uorf_table['averageORF2'] = averageORF2s
    uorf_table['averagechange'] = averagechanges
    uorf_table['logaveragechange'] = logaveragechanges
    uorf_table['zscore'] = stats.zscore(logaveragechanges)
    log_mean = stats.norm.mean(logaveragechanges)
    log_sigma = stats.norm.std(logaveragechanges)
    output = []
    for _, uORFrow2 in uorf_table.iterrows():
        joined_row = '\t'.join(map(str, uORFrow2))
        p_val = stats.norm.cdf(abs(uORFrow2['zscore'])) 
        uORF_changes_string = joined_row + "\t" + "\t" + str(p_val)
        output.append(uORF_changes_string)
    return (output)
    


# read in xtail output files
def create_table(name):
    df = pd.read_table(name, sep=",", index_col=0)
    df = df[["log2FC_TE_final", "pvalue_final", "pvalue.adjust"]]
    return df


# create output data frame
def create_output(args):
    annot = pd.read_table(args.uORF_annotation, sep=",", index_col=0)
    annot.drop(columns=["chromosome", "start", "stop", "strand", "gene_id", "strand", "ORF_length"], axis=1, inplace=True)
    return annot


def main():
    # store commandline args
    parser = argparse.ArgumentParser(description='Takes ORF annotation from merged ribotish output and computes the ribo_change parameter.')
    parser.add_argument("--uORF_reads", help='Path to input file with uORF reads')
    parser.add_argument("--ORF_reads", help='Path to input file with ORF reads')
    parser.add_argument("--uORF_annotation", help='Path to csv file containing uORF annotation')
    parser.add_argument("--output_csv_filepath", help='Path to write merged csv output')
    args = parser.parse_args()
    uorf_reads = pd.read_csv(args.uORF_reads)
    uorf_reads = uorf_reads[uorf_reads.columns.drop(list(uorf_reads.filter(regex='RNA')))]
    uorf_cols = uorf_reads.columns.values
    uorf_cols[0] = 'ID'
    uorf_reads.columns = uorf_cols
    uorf_reads_dict = uorf_reads.set_index('ID').T.to_dict('list')
    orf_reads = pd.read_csv(args.ORF_reads)
    orf_cols = orf_reads.columns.values
    orf_cols[0] = 'ID'
    orf_reads.columns = orf_cols
    orf_reads_dict = orf_reads.set_index('ID').T.to_dict('list')
    df_final = create_output(args)
    changes_list = uORF_changes(df_final, uorf_reads_dict, orf_reads_dict)
    changes_header = "coordinates\tgene_symbol\tstart_codon\ttranscript_id\tuORF_id\tavg_uorf_reads_c1\tavg_orf_reads_c1\tavg_uorf_reads_ratio_c2\tavg_orf_reads_c1\tribo_change\tlog2_ribo_change\tz_score\tp_value\n"
    changes_string = changes_header + '\n'.join(map(str, changes_list))
    f = open(args.output_csv_filepath, 'wt', encoding='utf-8')
    f.write(changes_string)


if __name__ == '__main__':
    main()
