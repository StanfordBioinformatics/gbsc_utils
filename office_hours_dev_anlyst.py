#!/usr/bin/env python

from random import shuffle

devs = [
        'Keith',
        'Paul',  
        'Amir', 
        'Nathan', 
        'Ziye']

analysts = [
            'Ramesh', 
            'Gao', 
            'Vandhana', 
            'Jina', 
            'Wenyu']

shuffle(devs)
shuffle(analysts)

while devs and analysts:
    dev = devs.pop()
    analyst = analysts.pop()

    print(f"{dev}   {analyst}")
