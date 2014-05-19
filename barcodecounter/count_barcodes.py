#!/usr/bin/env python

from optparse import OptionParser
import operator

class BarcodeCounter(object):
    def __init__(self, barcodesfile):
        self.barcodesfile = barcodesfile
        self.barcodes = {}
    def count(self):
        with open(self.barcodesfile) as f:
            for line in f:
                barcode = line.strip()
                self.barcodes.setdefault(barcode,0)
                self.barcodes[barcode] += 1
        sorted_barcodes = sorted(self.barcodes.iteritems(), key=operator.itemgetter(1), reverse=True)
        common=sorted_barcodes[0:49]
        for barcode in common:
            print "%s %s" % barcode

if __name__=='__main__':
    usage = '%prog barcodesfile.txt'
    parser = OptionParser(usage)
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    bc = BarcodeCounter(args[0])
    bc.count()
