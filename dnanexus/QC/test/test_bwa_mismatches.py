#!/usr/bin/env python

import os
import sys
import tempfile
import unittest

REGENERATE_GOLD_STANDARDS=False

test_dir = os.path.dirname(__file__)
data_dir = os.path.join(test_dir, 'data')
bin_dir = os.path.join(test_dir, '..', 'bin')
gold_standard_dir = os.path.join(test_dir, 'gold_standard')

class TestBWAMismatches(unittest.TestCase):

    def setUp(self):
        if not REGENERATE_GOLD_STANDARDS:
            self.tempdir = tempfile.mkdtemp()
        else:
            self.tempdir = gold_standard_dir
        self.tempfiles = []

    def tearDown(self):
        if not REGENERATE_GOLD_STANDARDS:
            while self.tempfiles:
                os.remove(os.path.join(self.tempdir, self.tempfiles.pop()))
            os.rmdir(self.tempdir)

        else:
            raise Exception("Set REGENERATE_GOLD_STANDARDS=False to run tests")

    def test_paired_end(self):
        self.check_sam_against_gold_standard('thirty_six')
        self.check_bam_against_gold_standard('thirty_six')

    def test_l_flag(self):
        # Should give same result with and without
        self.check_sam_against_gold_standard('thirty_six', l=36)
        self.check_bam_against_gold_standard('thirty_six', l=36)

    def test_single_read(self):
        self.check_sam_against_gold_standard('single_read')
        self.check_bam_against_gold_standard('single_read')

    def test_varied_length_reads(self):
        self.check_sam_against_gold_standard('varied_length', l=250)
        self.check_bam_against_gold_standard('varied_length', l=250)

    def check_bam_against_gold_standard(self, filename, l=None):
        self.check_xxx_against_gold_standard(filename, isSAM=False, l=l)

    def check_sam_against_gold_standard(self, filename, l=None):
        self.check_xxx_against_gold_standard(filename, isSAM=True, l=l)

    def check_xxx_against_gold_standard(self, filename, isSAM, l):
        if isSAM:
            infile = os.path.join(data_dir, filename+'.sam')
            outfile = os.path.join(self.tempdir, filename+'.sam.out')
        else:
            infile = os.path.join(data_dir, filename+'.bam')
            outfile = os.path.join(self.tempdir, filename+'.bam.out')
        gold_standard_file = os.path.join(gold_standard_dir, filename+'.out')

        self.tempfiles.append(outfile)

        cmd = os.path.join(bin_dir, 'bwa_mismatches')
        if isSAM:
            cmd += ' -S'
        if l:
            cmd += ' -l ' + str(l)
        cmd += ' -o ' + outfile + ' ' + infile
        if (os.system(cmd) != 0):
            raise Exception('Command failed: %s' % cmd)

        with open(outfile, 'r') as f:
            results = f.read()
        with open(gold_standard_file, 'r') as f:
            gold_standard = f.read()

        self.assertEqual(results, gold_standard)

if __name__ == '__main__':
    unittest.main()
