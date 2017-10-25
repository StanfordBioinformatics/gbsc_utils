#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stanford.edu
#2016-08-31
###

import itertools
import random
import sys
from argparse import ArgumentParser

#Make sure version of Python is >= 2.7.9
python_version = sys.version_info
version_err_msg = "You must be using a version of Python >= 2.7 to use this script."
if type(python_version) is tuple: #.i.e Python 2.6
		raise Exception(version_err_msg)
elif python_version.major == 2:
	if python_version.minor < 7:
		raise Exception(version_err_msg)

description = "Generates a rotation list for SCG Office Hours. Given the list of office hours representatives (stored in NAMES), uses the random.combination() method to select all combinations of size two from NAMES. Then, tries to randomize the rotation list by requiring that no two consecutive office hour sessions  have the same representative in both."
parser = ArgumentParser(description=description)
parser.parse_args()

def print_rotation(rotation):
	"""
	Args - rotation : list. Each element is a list or tuple of size 2 containing two names from the NAMES list.
	"""
	for i in rotation:
		print("{}\t{}".format(i[0],i[1]))

NAMES = ["Ramesh", "Gao", "Watson", "Paul", "Amir", "Keith", "Wendy", "Vandhana", "Priya"]
if len(NAMES) <4:
	raise Exception("There aren't enough names in the NAMES list for this rotation generator to work.")

gen = itertools.combinations(NAMES,2)
combs = list(gen)
random.shuffle(combs)

rotation = []
start = random.sample(combs,1)[0]
combs.remove(start)
rotation.append(start)

while combs:
	for i in range(len(combs)):
		pair = combs[i]
		if (pair[0] in rotation[-1]) or (pair[1] in rotation[-1]):
			if i != len(combs) -1:
				continue
		combs.remove(pair)
		rotation.append(pair)
		break

print_rotation(rotation)
	
