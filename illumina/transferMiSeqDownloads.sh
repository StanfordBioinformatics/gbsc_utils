#!/bin/bash

###
#AUTHOR: nathankw
#DATE  : Feb. 4, 2014
###
inputsDir=$1 
dest=$2 #either "pub" or "archive"
downloads=/srv/gs1/projects/scg/Downloads/results
oldPub=/srv/gs1/projects/scg/Archive/IlluminaRuns/
newPub=/srv/gsfs0/projects/seq_center/Illumina/PublishedResults
oldArchive=/srv/gs1/projects/scg/Archive/IlluminaRuns/2012/
newArchive=/srv/gsfs0/projects/seq_center/Illumina/RawDataArchive


monthsAr=(jan feb mar apr may jun jul aug sep oct nov dec)

logfile=$(pwd)/transferMiSeqDownloads_log_2014-02-04.txt
for i in ${inputsDir}/*
do
  if ! [[ -d $i ]]
  then
    continue
  fi
  run=$(basename $i)
	runLog=${inputsDir}/${run}_rsync.log
  year=${run:0:2} #get two digit year
  month=${run:2:2} #get two digit month
  month=${month#0} #trim off leading 0 if present
  monthText=${monthsAr[@]:$((${month} - 1)):1} #get month name (i.e. jan)
  yrmo=${year}${month}
  if [[ $yrmo -ge 1309 ]] 
  then #RSYNC TO $newPub
    outdir=${newPub}/20${year}/${monthText}/${run}
		if ! [[ -d $outdir ]]
		then
			mkdir -p $outdir
		fi
    echo "rsync'ing $run to $outdir"
    rsync -av ${i}/ $outdir &> $runLog
  else
  	###MV TO $oldPub
#  	outdir=${oldPub}/20${year}/${monthText}
  	outdir=${oldPub}/20${year}/${monthText}/${run}
		if ! [[ -d ${outdir} ]]
		then
			mkdir -p $outdir
		fi
#  	###VERIFY THAT $outdir DOESN'T EXIST YET SO NO FEAR OF OVERWRITING ANYTHING
#  	if [[ -d ${outdir}/${run} ]]
#  	then
#  	  echo "Can't move $run to $outdir b/c ${outdir}/${run} already exists!!" | tee -a $logfile
#  	  continue
#  	fi
  	###
#  	echo "Moving $run to $outdir"
		echo "rsync'ing $run to $outdir"
#  	mv $i $outdir
		rsync -av ${i}/ $outdir &> $runLog
	fi
done




###The code below was used to fix a case with rsync.  Originally, I rsync'd the folders w/o a trailing /, meaning 
### that the directory was nested inside its destination folder. This script below moved the contents of the 
### nested folder up a level, then removed the empty nested directory.  For example, given:
	###              /path/to/somedir/somedir/file1.txt
  ###              /path/to/somedir/somedir/file2.txt           
### the result would be
####               /path/to/somedir/file1.txt
##                 /path/to/somedir/file2.txt
#source /srv/gs1/software/nathankw/bash/utils.sh
#for i in *SPENSER*
#do
#  if ! [[ -d $i ]]
#  then
#    continue
#  fi
#  cd $i
#  if [[ -d $i ]]
#  then
#    echo $i
#    mv $i/* .
#    emp=$(dirEmpty $i)
#    if [[ $emp -eq 1 ]]
#    then
#     rm -rf $i
#    else
#     echo "Cant remove directory ${i}!!!"
#     exit
#    fi
#  fi
#  cd ..
#done
