#!/usr/bin/env python
'''This script takes n number of input files generated by
ribotaper and creates a new data frame containing only
the uORF information. The input must be in the
form <file1> <file2> <file3> ... min_length max_length.
The resulting data frame is stored as csv file
- mammalian uORF length at least 9nt
(https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2669787/)
- Should we set (min/)max length?
--> (https://link.springer.com/content/pdf/10.1186/1471-2164-10-162.pdf)
'''

import pandas as pd
import re
import argparse


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
    df_dropped = df_uORFs[["gene_id", "gene_symbol", "transcript_id", "strand", "ORF_id_gen", 'ORF_length']]
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
    for name in args.ribotaper_ORFs_path:
        df_sub = drop_cols(name)
        df_final = df_final.append(df_sub)

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
            df_final = df_final[df_final['ORF_length'] >= int(input_args[-2])]
            
        if args.max_length is not None:
            df_final = df_final[df_final['ORF_length'] <= int(input_args[-1])]
    return df_final


def main():
    # store commandline args
    parser = argparse.ArgumentParser(description='Converts ribotaper output to new data frame containing only
the uORF information.')
    parser.add_argument("-u","--ribotaper_ORFs_path", help='Path to ribotaper ORF file (ORFs_max_filt)')
    parser.add_argument("-o","--output_csv_filepath", help='Path to write merged csv output')
    parser.add_argument("-m","--min_length", default=None, help='Minimal uORF length')
    parser.add_argument("-l","--max_length", default=None, help='Maximal uORF length')
    args = parser.parse_args()
    # make sure that min_length and max_length are given
    #assert type(int(input_args[-1])) == int, "The last argument is not a number!"
    #assert type(int(input_args[-2])) == int, "The second to last argument is not a number!"
    output = create_output(args)
    # get some general info on output
    print(output.describe(include='all'))
    # write output to csv file
    output.to_csv(arg.output_csv_filepath)


if '__name__' == '__main__':
    main()
