#!/usr/bin/env python3

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

if devs or analysts:
    byes = ','.join(devs + analysts)
    print("~~~~~~")
    print(f"Bye: {byes}.")
