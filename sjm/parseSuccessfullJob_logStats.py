###
#AUTHOR: Nathaniel Watson
###

def parse(infile):
	dico = {}
	fh = open(infile,'r')
	for line in fh:
		if line.startswith("Successful jobs:"):
			break
	for line in fh:
		if line.startswith("Failed jobs:"):
			break
		line = line.strip("\n")
		if not line:
			break
		line = line.split()
		name = line[0] #job name
		jid = line[1] #job id
		jid = jid.lstrip("(")
		jid = jid.rstrip("):")
		if len(jid) <= 6:
			continue #don't count localhost jobs (PID). 6 because the max pid number currently defined in /proc/sys/kernel/pid_max is 245760.
		dico[name] = {}
		dico[name]["jid"] = jid
		wcTime = line[2]
		dico[name]["wc_time"] = wcTime
		cpuTime = line[3].lstrip("(")
		dico[name]["run_time"] = cpuTime
		mem = line[5].strip()
		vmem,swapMem = mem.split("/") #both figures are in MB
		dico[name]["virtual_mem"] = int(vmem) #max virtual memory usage
		dico[name]["swap_mem"] = int(swapMem) #max swap memory usage
	return dico

def maxVmem(dico):
	vmems = []
	for jobname in dico:
		vmems.append(dico[jobname]["virtual_mem"])
	return max(vmems)



import argparse

description = ""
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Input SJM log file.")

args = parser.parse_args()
infile = args.infile

dico = parse(infile)
mvm = maxVmem(dico)
print(mvm)
