#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# nathankw@stanford.edu
###

"""
Given a multi-FASTA file, extracts records of interest into a new FASTA file.
"""

import argparse

from gbsc_utils.fasta import fasta

def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--infile", required=True, help="The input FASTA file.")
    parser.add_argument("-o", "--outfile", required=True, help="The output FASTA file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--name", help="""The name of a record, which comes from the title line
        of a FASTA record. The name should not include the beginning '>' character, and should only
        consist of the first field on the line before any spacing. For example, if the title line is
        >Chr1 chromosome, then the name of the record is 'Chr1'.""")
    group.add_argument("-f", "--names-file", help="""Input file containing one or more record names 
        (one per line).  The name format is the same as described above for the --record option.""")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    fout = open(args.outfile, "w")
    if args.name:
        names = [args.name]
    else:
        names = []
        rfh = open(args.names_file)
        for line in rfh:
            line = line.strip()
            if not line:
                continue
            names.append(line)
        rfh.close()

    index = fasta.ByteIndex(args.infile)
    for i in names:
        fout.write(index.getRawRecord(i))
    fout.close()

if __name__ == "__main__":
    main() 


