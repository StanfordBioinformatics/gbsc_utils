#! /usr/bin/env python

# reverse_complement.py
# Takes a file containing a list of sequences and
# outputs a file with the reverse complements

import StringIO
from optparse import OptionParser

class ReverseComplement:
    complementDict = {
        'C': 'G',
        'c': 'g',
        'G': 'C',
        'g': 'c',
        'A': 'T',
        'a': 't',
        'T': 'A',
        't': 'a',
        }

    def __init__(self, inputFile, outputFile, doPrintLabel):
        self.inputFile = inputFile
        self.outputFile = outputFile
        self.doPrintLabel = doPrintLabel

    def reverse(self):
        with open(self.inputFile) as f:
            with open(self.outputFile, 'w') as o:
                for rawLine in f.readlines():
                    lineIn = self._line_strip(rawLine)
                    lineOut = self._line_reverse_complement(lineIn)\
                        +self._line_name(lineIn)\
                        +'\n'
                    o.write(lineOut)

    def _line_strip(self, line):
        return line.strip()

    def _line_reverse_complement(self, line):
        return self._line_reverse(self._line_complement(line))

    def _line_reverse(self, line):
        return line[::-1]

    def _line_complement(self, line):
        buf = StringIO.StringIO()
        for letter in line:
            buf.write(self.complementDict[letter])
        return buf.getvalue()

    def _line_name(self, line):
        if self.doPrintLabel:
            return ' generated_from_barcode_'+line
        else:
            return ''

if __name__=="__main__":
    outputFile = None
    inputFile = None

    usage = "%prog [options] infile"
    parser = OptionParser(usage=usage)
    parser.add_option('-l', 
                      '--label', 
                      action='store_true',
                      default=False,
                      help='Generate line labels')

    parser.add_option('-o',
                      '--output',
                      dest = 'outputFile',
                      help='write output to FILE',
                      metavar='FILE')

    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Need an input file")

    if len(args) > 1:
        parser.error("Too many input arguments")

    inputFile = args[0]
    outputFile = opts.outputFile
    if not outputFile:
        fileParts = inputFile.split('.')
        if len(fileParts) == 1:
            fileParts.append('REVERSE_COMPLEMENT')
        else:
            fileParts.insert(-1, 'REVERSE_COMPLEMENT')
        outputFile = '.'.join(fileParts)

    rc = ReverseComplement(inputFile, outputFile, opts.label)
    rc.reverse()
