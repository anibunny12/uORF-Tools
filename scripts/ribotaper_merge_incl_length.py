#!/usr/bin/env python
'''This script takes n number of input files generated by
ribotaper and creates a new data frame containing only
the uORF information and writes it as csv and bed6 format files.
'''

import pandas as pd
import re
import argparse
import numpy as np
import os

# function to read in ribotaper output files ORFs_max_filt
def create_table(name):
    df = pd.read_table(name)
    return df


# function to select only uORFs
def keep_uORFs(df):
    df = create_table(df)
    df_uORFs = df[df["category"] == "uORF"]
    return df_uORFs


# function to keep only certain columns
def drop_cols(df_uORFs):
    df_uORFs = keep_uORFs(df_uORFs)
    df_dropped = df_uORFs[["gene_id", "gene_symbol", "transcript_id", \
                           "strand", "ORF_id_gen", 'ORF_length']]
    return df_dropped


# function to get chromosome name
def chrom_name(column):
    chrom = []
    for i in column:
        match = re.findall("chr[0-9MXY]+", i)
        for a in match:
            chrom.append(a)
    return chrom


# function to get start position
def start(column):
    start = []
    for i in column:
        match = re.findall("_(.+)_", i)
        for a in match:
            start.append(a)
    return start


# function to get stop position
def stop(column):
    stop = []
    for i in column:
        match = re.findall("_([0-9]+)$", i)
        for a in match:
            stop.append(a)
    return stop


# function to create final data frame
def create_output(args):
    # create empty data frame to append to later
    df_final = pd.DataFrame()

    # Create data frame from all input files
    for name in args.ribotaper_files:
        if os.stat(name).st_size == 0:
            df_sub = drop_cols(name)
            df_new = pd.read_csv(df_sub, sep = "\t")
            for new_index, new_row in df_new.iterrows():
                 #check if entry with overlapping coordinates already exists
                 orf_range = range((new_row.start -1), (new_row.end + 1))
                 orf_set = set(orf_range)
                 orf_length = new_row.end - new_row.start
                 for index, row in df_final.iterrows():
                     oorf_range = range((row.start - 1), (row.end + 1))
                     oorf_set = set(oorf_range)
                     oorf_length = new_row.end - new_row.start
                     intersect = orf_range.intersection(oorf_range)
                     if not intersect:
                         #just add new_row to df_final
                         df_final.loc[len(df_final)] = new_row
                     else:
                         #if new entry is longer, replace the original entry
                         if orf_length > oorf_length:
                             df_final.loc[index]= new_row
                           
            #df_final = df_final.append(df_sub, sort=True)

    # Cleaning up data frame
    df_final.drop_duplicates(subset="ORF_id_gen", inplace=True)
    df_final.reset_index(inplace=True)
    df_final.drop(["index"], axis=1, inplace=True)

    # add chromosome, start, and stop positions as columns to data frames
    df_final["chromosome"] = chrom_name(df_final["ORF_id_gen"])
    df_final["start"] = start(df_final["ORF_id_gen"])
    df_final["stop"] = stop(df_final["ORF_id_gen"])

    # Filter min and max uORF lengths
    if args.min_length is not None:
    df_final = df_final[df_final['ORF_length'] >= int(args.min_length)]

    if args.max_length is not None:
    df_final = df_final[df_final['ORF_length'] <= int(args.max_length)]
    return df_final

def set_uORFids(args):
        tid_dict = {}
        uORFids = []
        for index, row in args.iterrows():
            if row.transcript_id in tid_dict:
                tindex=tid_dict[row.transcript_id]
                tid_dict[row.transcript_id]=tindex + 1
            else:
                tindex = 1
                tid_dict[row.transcript_id] = tindex
            uORFid = row.transcript_id + '.' + str(tindex)
            uORFids.append(uORFid)
        m = np.asarray(uORFids)
        args["uORFids"]=m
        return(args)

def make_uORFs_bed(args):
    uORFsString = ""
    for index, row in args.iterrows():
        uORFString=row.chromosome + "\t" + row.start + "\t" + row.stop + "\t" + row.uORFids + "\t0\t" + row.strand + "\n"
        uORFsString= uORFsString + uORFString
    return(uORFsString)

def main():
    # store commandline args
    parser = argparse.ArgumentParser(description='Converts ribotaper output to new data frame\
                                     containing only the uORF information.')
    parser.add_argument('ribotaper_files', nargs='*', metavar='ribotaper', help='Path to ribotaper ORF file (ORFs_max_filt)')
    parser.add_argument("--output_csv_filepath", help='Path to write \
                        merged csv output')
    parser.add_argument("--output_bed_filepath", help='Path to write \
                        merged bed6 output')
    parser.add_argument("--min_length", default=None, help='Minimal uORF \
                        length')
    parser.add_argument("--max_length", default=None, help='Maximal uORF \
                        length')
    args = parser.parse_args()
    # make sure that min_length and max_length are given
    uorfsframe = create_output(args)
    # get some general info on output
    #print(output.describe(include='all'))
    # write output to csv file
    uorfsframe.to_csv(args.output_csv_filepath)
    uORFsdf=set_uORFids(uorfsframe)
    uORFsbed=make_uORFs_bed(uORFsdf)
    f = open(args.output_bed_filepath, 'wt', encoding='utf-8')
    f.write(uORFsbed)


if __name__ == '__main__':
    main()
