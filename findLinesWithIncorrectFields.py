###
#AUTHOR: Nathaniel Watson
###

from argparse import ArgumentParser
import os
import re

def g(lineLen,threshold):
	if lineLen > threshold:
		return True

def ge(lineLen,threshold):
	if lineLen >= threshold:
		return True

def l(lineLen,threshold):
	if lineLen < threshold:
		return True

def le(lineLen,threshold):
	if lineLen <= threshold:
		return True

def eq(lineLen,threshold):
	if lineLen == threshold:
		return True

def ne(lineLen,threshold):
	if lineLen != threshold:
		return True

operators = ['<','<=','>','>=','=','!=']
OUTPUTFILE_SAME = "-1" #for use with the --outfile option
reg = re.compile(r'(?P<op>[<>=!]+)(?P<t>\d+)') #op - operator; t - threshold (pertains to --threshold argument)

description = "Checks for lines with the incorrect number of fields. The user specifies a number of fields (let's call it the 'threshold') and an operator belonging to the set {operators} (Let's call the chosen operator 'op'). For each line, the number of fields in that line are calculated (call it numFields). If the test (expression) 'numFields op threshold' is true, then the line in question is printed to stdout. At the end of the program, a distrubtion of the number of lines having specific field lengths is printed. Empty lines are skipped.".format(operators=operators)
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The input text file")
parser.add_argument('-d','--delimiter',default='\t',help="The delimiter separating fields in --infile. Default is r'\t'")
parser.add_argument('-t','--threshold',required=True,help="A number-of-fields threshold that indicates what lines to report. Format is one of the operators in the set {operators} followed by a number. For example, >10 means to report all lines with greater than 10 fields.".format(operators=operators))
parser.add_argument('-o','--outfile',nargs="?",const=OUTPUTFILE_SAME,help="Write all lines to this output file that fail the test described in the description of the program. Passing no value to this option indicates that the output file name is the same as the input file name, in which case the original will not be saved.") 

args = parser.parse_args()
delim = args.delimiter
infile = args.infile
renameInfile = False #True when user wants output file name to be same as input file. In this case, the input file is renamed at the beginning of the program, and deleted at the end
outfile = args.outfile
if outfile:
	if outfile == OUTPUTFILE_SAME: #then output file name should be same as input file name. rename original input file, and delete it at the end of the program
		renameInfile = True #at end of program
		outfile = infile + ".output"
	fout = open(outfile,'w')
groups = reg.search(args.threshold).groupdict()
op = groups['op']
t = int(groups['t'])
#print("Op is {op} and t is {t:d}".format(op=op,t=t))
if op == "<":
	func = l
elif op == "<=":
	func = le
elif op == ">":
	func = g
elif op == ">=":
	func = ge
elif op == "=":
	func = eq
elif op == "!=":
	func = ne
else:
	raise parser.error("Invalid operator specifier. See --threshold")
#print("Operator funciton choses is {f}".format(f=func.__name__))
lldict = {} #line length dict (number of fields are keys and values are #occurrences of lines having that number of fields)

fh = open(infile,'r')
lineCount = 0 #count of only data lines
writeCount = 0
actualLineCount = 0 #count of data lines + empty lines
for line in fh:
	actualLineCount += 1	
	line = line.strip("\n")
	if not line:
		continue
	lineCount += 1
	line = line.split(delim)
	ll = len(line) #line length	
#	print("{ll} : {t}".format(ll=ll,t=t))
	if func(ll,t):
		print("{lineNum}: {line}".format(lineNum=actualLineCount,line=line))	
	else:
		if outfile:
			fout.write(delim.join(line) + "\n")
			writeCount += 1
	try:
		lldict[ll] += 1
	except KeyError:
		lldict[ll] = 1
#	if ll not in lldict:
#		lldict[ll] = 0
#	lldict[ll] += 1
fh.close()
if renameInfile:
	os.rename(outfile,infile)
	outfile = infile
print("\n")
print(lldict)
if outfile:
	fout.close()
	print("\n")
	print("Wrote {writeCount}/{lineCount} lines to {outfile}".format(writeCount=writeCount,lineCount=lineCount,outfile=outfile))
