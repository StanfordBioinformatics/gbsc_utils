#!/usr/bin/env python
import itertools
import random

def print_rotation(rotation):
	for i in rotation:
		print("{}\t{}".format(i[0],i[1]))

NAMES = ['Ramesh', 'Watson', 'Paul', 'Isaac', 'Amin', 'Keith']
if len(NAMES) <4:
	raise Exception("There aren't enough person in the NAMES list for this rotation generator to work.")

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
	print(combs)

print_rotation(rotation)
	
