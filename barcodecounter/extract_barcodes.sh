#!/bin/bash

if [ $# -eq 0 ] || [ $# -gt 2 ]
    then
    echo "Usage:"
    echo "extract_barcodes.sh inputfile [outputfile]"
    exit 1
fi
infile=$1
if [ $# -gt 1 ]
    then 
    outfile=$2
    else
    outfile=${infile}.barcodes
fi
temp=${infile}.tmp

re_barcode='[ACGTN]\+$'
re_header='^@.*:'$re_barcode

# Extract the fastq header lines
grep $re_header $infile > $temp

# Estract the barcodes from the header lines
grep -o $re_barcode $temp > $outfile

rm $temp
