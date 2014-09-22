###
#AUTHOR: NATHANIEL WATSON
###

#pub=/srv/gsfs0/projects/seq_center/Illumina/PublishedResults
pub=/srv/gs1/projects/scg/Archive/IlluminaRuns

function help {
	echo "DESCRIPTION:"
	echo "Looks in all sequencing run folders that reside within the provided published results directory (-p) and tabulates the sizes of each file that matches to supplied regular expression (-r)."
	echo "Optionally will delete (-d) any of those files matching the regex. NOTE: It is not recommended to pass the -d option until you have verifed in the log file those files that matched the regex."
  
	echo "ARGS:"
	echo "  -p The published directory that contains the year folders. Default is ${pub}."
	echo "  -l The logfile name.  Will contain a listing of all files that match the supplied regex as will as their sizes."
	echo "  -r Regex. Be sure to put quotation marks (single or double) around this arguments value."
	echo "  -d Delete any files matching regex. Not recommended to use until after you have performed a dry run and looked at the log file. The log file will contain a listing of all files that matched the supplied reges (-r)."

}

rem= #flag for removal. Starts off false.
while getopts "hp:l:r:d" opt
do
	case $opt in 
		p) pub=$OPTARG;;
		l) outfile=$OPTARG;;
		r) regex=$OPTARG;;
		d) rem=1;;
		h) help
			 exit;;
	esac
done

if [[ ${#@} -eq 0 ]]
then
	help
fi

echo "Regex is #${regex}#"
exit

for year in $(ls -d ${pub}/* 2>/dev/null)
do
	if ! [[ $year =~ [0-9]{4} ]]
	then
		continue
	fi
	for month in $(ls -d $year/* 2>/dev/null)
	do
		if ! [[ $month =~ [a-zA-Z]+ ]]
		then
			continue
		fi
		for run in $(ls -d $month/* 2>/dev/null)
		do
			for unsorted in $(ls ${run}/${regex} 2>/dev/null)
		  do
				echo $(ls -lh $unsorted) >> $outfile
				if [[ -n $rem ]]
				then
					rm -rf $unsorted
				fi
			done
			for lane in $(ls -d ${run}/L[1-8] 2>/dev/null)
			do
				for unsorted in $(ls ${lane}/${regex} 2>/dev/null)
				do
					echo $(ls -lh $unsorted) >> $outfile
					if [[ -n $rem ]]
					then
						rm -rf $unsorted
					fi
				done
			done
		done
	done
done
