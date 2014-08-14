#!/bin/bash

###
#AUTHOR: Nathaniel Watson
###

fastqRecCount() {
	fqfile=$1
	lc=$(wc -l $fqfile)
	lc=${lc% *}
	echo -n -e "$(basename $fqfile)\t"
	echo "scale=2;${lc}/4" | bc -l
}	


dirEmpty() {
	dirname=$1
	count=$(ls -A $dirname)
	if [[ ${#count} -eq 0 ]]
  then
    echo 1
  else
	  echo 0
  fi
}
