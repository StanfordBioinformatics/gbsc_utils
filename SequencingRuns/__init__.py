import os
import json

curdir = os.path.dirname(__file__)
confFh = open(os.path.join(curdir,"conf.json"))
conf = json.load(confFh)
