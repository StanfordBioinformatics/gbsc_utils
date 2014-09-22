###
#AUTHOR:NATHANIEL WATSON
###
#this is an example for how to write a shell script with getopts


function help {
	echo "howdy"
}

while getopts "a:h" opt
do
	case $opt in 
		a) echo $OPTARG
#			 echo $OPTIND
			 ;;
		h) help
			 exit
			 ;;
	esac
done

if [[ ${#@} -eq 0 ]]
then
  help
fi

#echo positional args
echo ${@:${OPTIND}}



