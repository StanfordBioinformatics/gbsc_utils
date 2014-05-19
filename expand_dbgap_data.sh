#!/bin/bash

usage="Usage: \nuntar_all.sh ROOTDIR\nrecursively finds and extracts all tar files under ROOTDIR"

ROOTDIR=$1

if [ -z "$ROOTDIR" ] 
then echo -e $usage
fi

# Unextracted files are moved here, then deleted if no errors
DUMPROOT=$ROOTDIR/_extracted

tarfiles='.'
gzfiles='.'

# Sum of all return codes to test for overall success
retcodes=0

# Iterate as long as *.tar or *.gz are found
while [ "${tarfiles}" ] || [ "${gzfiles}" ]
do
    tarfiles=$(find $ROOTDIR -path $DUMPROOT -prune -o -name "*.tar" -print); retcodes=$(($retcodes + $?))
    gzfiles=$(find $ROOTDIR -path $DUMPROOT -prune -o -name "*.gz" -print); retcodes=$(($retcodes + $?))
    
    for file in $tarfiles
    do echo Expanding $file...
	tar -xf $file -C $(dirname $file); retcodes=$(($retcodes + $?))
	echo "...moving to $DUMPROOT"
	dest=$DUMPROOT/$(dirname $file)
	mkdir -p $dest; retcodes=$(($retcodes + $?))
	mv $file $dest; retcodes=$(($retcodes + $?))
    done
    
    for file in $gzfiles
    do echo Expanding $file...
	outfile=$(dirname $file)/$(basename $file .gz)
	gunzip -c $file > $outfile; retcodes=$(($retcodes + $?))
	echo "...moving to $DUMPROOT"
	dest=$DUMPROOT/$(dirname $file)
	mkdir -p $dest; retcodes=$(($retcodes + $?))
	mv $file $dest; retcodes=$(($retcodes + $?))
    done
done

# If successful, clean up compressed and tarred files
if [ $retcodes -eq 0 ] 
then
    echo "Deleting unexpanded files in $DUMPROOT ..."
    rm -r $DUMPROOT
    echo "...Done"
fi