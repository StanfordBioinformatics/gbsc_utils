#!/usr/bin/env python

from argparse import ArgumentParser
import errno
import os
import random
import subprocess

def run(outdir, numchr, chrlength, numreads, readlength, alphabet):

    reference_dir = os.path.join(outdir, 'reference')
    mapping_dir = os.path.join(outdir, 'mapping')

    reference_file = os.path.join(reference_dir, 'reference.fa')
    reads_file = os.path.join(outdir, 'reads.fa')
    sai_file = os.path.join(mapping_dir, 'reads.sai')
    sam_file = os.path.join(mapping_dir, 'reads.sam')
    bam_file = os.path.join(mapping_dir, 'reads.bam')

    mkdir_p(outdir)
    mkdir_p(reference_dir)
    mkdir_p(mapping_dir)

    chromosomes = make_reference(numchr, chrlength, alphabet, reference_file)
    index_reference(reference_file)
    
    make_reads(readlength, numreads, chrlength, numchr, chromosomes, reads_file)
    map_reads(sai_file, sam_file, reads_file, reference_file)
    make_bam(sam_file, bam_file)

def mkdir_p(outdir):
    try:
        os.makedirs(outdir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(outdir):
            pass
        else: raise

def make_reference(numchr, chrlength, alphabet, reference_file):
    with open(reference_file, 'w') as f:
        chromosomes = {}
        for i in range(0,numchr):
            chromosomes[i] = random_sequence(chrlength, alphabet)
            f.write('>chr%s\n' % (i+1))
            f.write(chromosomes[i]+'\n')
    return chromosomes

def random_sequence(chrlength, alphabet):
    s = ''
    for i in range(0, chrlength):
        s += alphabet[random.randint(0, len(alphabet)-1)]
    return s

def index_reference(reference_file):
    cmd = 'bwa index %s' % reference_file
    with open('/dev/null', 'w') as devnull:
        subprocess.check_call(cmd, stdout=devnull, stderr=devnull, shell=True)

def make_reads(readlength, numreads, chrlength, numchr, chromosomes, reads_file):
    assert len(chromosomes) == numchr
    if not readlength < chrlength:
        raise Exception("Read length %s is greater than chromosome length %s" % (readlength, chrlength))
    with open(reads_file, 'w') as f:
        for i in range(0, numreads):
            pick_chr = random.randint(0, numchr - 1)
            pick_readstart = random.randint(0, chrlength - readlength - 1)
            f.write('>%s\n' % i)
            f.write('%s\n' % chromosomes[pick_chr][pick_readstart:pick_readstart+readlength])

def map_reads(sai_file, sam_file, reads_file, reference_file):

    with open('/dev/null', 'w') as devnull:
        with open(sai_file, 'w') as sai:
            cmd = "bwa aln %s %s" % (reference_file, reads_file)
            subprocess.check_call(cmd, stdout=sai, stderr=devnull, shell=True)
        with open(sam_file, 'w') as sam:
            cmd = "bwa samse %s %s %s" % (reference_file, sai_file, reads_file)
            subprocess.check_call(cmd, stdout=sam, stderr=devnull, shell=True)

def make_bam(sam_file, bam_file):
    cmd = "samtools view -bS %s -o %s" % (sam_file, bam_file)
    with open('/dev/null', 'w') as devnull:
        subprocess.check_call(cmd, stderr=devnull, stdout=devnull, shell=True)

def parse_commandline_args():
    args = get_default_args()
    new_args = initialize_parser().parse_args()
    overwrite_if_set(args, new_args)
    return args

def initialize_parser():
    parser=ArgumentParser('generate a very small synthetic genome for testing')
    parser.add_argument('--outdir')
    parser.add_argument('--numchr')
    parser.add_argument('--chrlength')
    parser.add_argument('--numreads')
    parser.add_argument('--readlength')
    parser.add_argument('--alphabet')
    return parser

def overwrite_if_set(args, new_args):
    if new_args.outdir:
        args['outdir'] = new_args.outdir
    if new_args.numchr:
        args['numchr'] = int(new_args.numchr)
    if new_args.chrlength:
        args['chrlength'] = int(new_args.chrlength)
    if new_args.numreads:
        args['numreads'] = int(new_args.numreads)
    if new_args.readlength:
        args['readlength'] = int(new_args.readlength)

    if new_args.alphabet:
        args['alphabet'] = new_args.alphabet
    return args

def get_default_args():
    return {
        'outdir': 'output',
        'numchr': 3,
        'chrlength': 100,
        'numreads': 10,
        'readlength': 20,
        'alphabet': 'acgt',
        }

if __name__=='__main__':
    args = parse_commandline_args()
    run(
        outdir=args['outdir'],
        numchr=args['numchr'],
        chrlength=args['chrlength'],
        numreads=args['numreads'],
        readlength=args['readlength'],
        alphabet=args['alphabet'],
        )
