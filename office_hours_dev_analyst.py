#!/usr/bin/env python

from random import shuffle

devs = [
        'Keith',
        'Paul',  
        'Amir', 
        'Daniel',
        'Tao',
        'Arash']

analysts = [
            'Ramesh', 
            'Vandhana', 
            'Jina', 
            'Pratima',
            'Yan']

shuffle(devs)
shuffle(analysts)

while devs and analysts:
    dev = devs.pop()
    analyst = analysts.pop()

    print(f"{dev}   {analyst}")
