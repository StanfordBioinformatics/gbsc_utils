#AUTHOR: Nathaniel Watson
#DATE  : April 27, 2015

#DESCRIPTION:
# Given an Illumina Run directory where the reads have already been demultiplexed, looks for any lane that has more than one sample on it, in which case
# the folowing fields are printed:
#		1) run name 
#		2) project  (as specified in the SampleSheet.csv)
#		3) samples  (as specified in the SampleSheet.csv)

run=$1
for i in $(ls -d ${run}/Unaligned* 2>/dev/null)
do
	for project in $(ls -d ${i}/Project* 2>/dev/null)
	do
		samples=$(ls -d ${project}/Sample_* 2>/dev/null)
		samples=($samples)
		if [[ ${#samples[@]} -ge 2 ]]
		then
			echo $run $project $samples
		fi
	done
done
