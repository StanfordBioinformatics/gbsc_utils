#!/usr/bin/env python

###
#Nathaniel Watson
#2016-09-12
#nathankw@stanford.edu
###

import os
import sys
import fnmatch
from argparse import ArgumentParser
import shutil
import pdb


def getDirSize(dir_path):
	"""
	Function : Recursively calculates the size of all files in bytes in the provided directory.
	Args     : dir_path - The path to a directory.
	Returns  : int.
	"""
	tot_bytes = 0
	for root, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			path = os.path.join(root,f)
			tot_bytes += os.path.getsize(path)
	return tot_bytes

LIST_ACTION_NAME = "list"
DELETE_ACTION_NAME = "delete"

TB_EXPONENT = 4
GB_EXPONENT = 3
MB_EXPONENT = 2
KIBIBYTE = 1024

description = """Prints the total size of all files and directories that recursively match the given patterns. The size appropriately reported in TB, GB, or MB, depending on the total size. If any actions are specified via the --actions argument, then \
those corresponding actions will also take place. Currently, the only actions defined are the "list" and "delete" actions, where the former lists each found file, and the latter deletes each found file."""

parser = ArgumentParser(description=description)
parser.add_argument('-d',"--directory",required=True,help="Directory to start the recursive search.")
parser.add_argument('-e',"--extensions",required=True,nargs="+",help="A file extension for file matching.")
parser.add_argument('-a',"--actions",nargs="+",required=True,choices=["list","delete"],help="Defines what to do when the files are found. The options are: 1) list - Print the name of each found file, and 2) delete - Delete the found files. Actions can be combined.")

args = parser.parse_args()

directory = args.directory
extensions = args.extensions
actions = args.actions

tot_bytes = 0
matches = []
dont_list_dirs = [] #a list of dirs that were found to be deleted recursivly. No need to travers their contents. 
for root, dirnames, filenames in os.walk(directory):
	if root in dont_list_dirs:
		continue
	for ext in extensions:
		for f in filenames:
			if f.endswith(ext):
				path = os.path.join(root, f)
				matches.append(path)
				tot_bytes += os.path.getsize(path)
		for dname in dirnames:
			path = os.path.join(root,dname)
			if path in dont_list_dirs:
				continue
			if dname.endswith(ext):
				matches.append(path)
				dont_list_dirs.append(path)
				tot_bytes += getDirSize(path)
			
				
tot_bytes = float(tot_bytes)
size_suffix = "TB"
tot_size = tot_bytes/KIBIBYTE**TB_EXPONENT
if tot_size < 1:
	size_suffix = "GB"
	tot_size = tot_bytes/KIBIBYTE**GB_EXPONENT
	if tot_size < 1:
		size_suffix = "MB"
		tot_size = tot_bytes/KIBIBYTE**MB_EXPONENT

if LIST_ACTION_NAME in actions:
	for m in matches:
			print("Found {filename}.".format(filename=m))

print("Total size of found files: {tot_size:.2f}{size_suffix}.".format(tot_size=tot_size,size_suffix=size_suffix))

if DELETE_ACTION_NAME in actions:
	for m in matches:
		if os.path.isdir(m):
			print("Removing directory {m}.".format(m=m))
			shutil.rmtree(m)
		else:
			print("Removing file {m}.".format(m=m))
			os.remove(m)
	
