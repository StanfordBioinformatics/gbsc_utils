#!/usr/bin/python

import gc, re, sys
gc.disable()
pad, wig, stripSuffix, files = int(sys.argv[1]), sys.argv[2].lower() == 'wig', sys.argv[3] != '0', sys.argv[4:]
sow = sys.stdout.write

def processData(pad, lx, rx, ps):
    # step in order through the start (ps) and stop (stops) positions
    # for the intervals. at the start of each interval, increment the
    # count, and decrement it at the end of each interval. add each
    # change "event" to the list of events (events), except for stacked
    # events (same start or stop), in which case just adjust the
    # count.
    stops = [ps[p]+pad for p in xrange(lx, rx)]
    events, c, px, sx, = [(-1, -1)], 0, lx, 0
    while px < rx:
        if stops[sx] < ps[px]: sx, c, p = sx+1, c-1, stops[sx]
        else:                  px, c, p = px+1, c+1, ps[px]
        if p == events[-1][0]: events[-1] = (p, c)
        else: events.append((p, c))

    # all that remains are stops. with a little cleverness, this could
    # probably be combined with the previous loop.
    for p in stops[sx:]:
        c -= 1
        if p == events[-1][0]: events[-1] = (p, c)
        else: events.append((p, c))

    # eliminate events that don't actually change the count.
    nEvents = [events[1]]
    for d in events[2:]:
        if d[1] != nEvents[-1][1]: nEvents.append(d)

    return nEvents

def dumpSgrData(seq, pad, lx, rx, ps):
    if lx+1 == rx:
        # common case
        print '%s\t%d\t%d'%(seq, ps[lx], 1)
        print '%s\t%d\t%d'%(seq, ps[lx]+pad, 0)
        return

    events = processData(pad, lx, rx, ps)

    fs = '%s\t%%d\t%%d\n'%seq
    for e in events: sow(fs%e)
        
def dumpWigData(seq, pad, lx, rx, ps):
    # wig's bed format uses zero-based half intervals, so we need to subtract 1 from the start positions.
    if lx+1 == rx:
        # common case
        print '%s\t%d\t%d\t%d'%(seq, ps[lx]-1, ps[lx]+pad-1, 1)
        return

    events = processData(pad, lx, rx, ps)

    fs = '%s\t%%d\t%%d\t%%d\n'%seq
    for x in xrange(len(events)-1):
        sow(fs%(events[x][0]-1, events[x+1][0]-1, events[x][1]))


# eland_formats is a list of (func, suffix) pairs. Func is invoked to read a
# file if the file name ends with suffix. Need to be careful about
# ordering in the case where names "nest", e.g. suppose we have these
# two kinds of names:
#  s_1_foo.txt
#  s_1_foofoo.txt
# We need to test for foofoo first, so put it before foo.txt in this
# list.
eland_formats = []

# eland_export format    
export_sample = '''\
FC30M30	111308	8	1	1183	1854		2	ATTTATTTTCTCTATAAATAACCACTTTTATCTTT	XXXXXXXXXXXXX[E[RXXYXXXRXXXXXYCSSSS	mm_ref_chr6.fa		133057049	R	14G15G4	12	0			-75	F	Y
FC30M30	111308	8	1	1724	1324		2	CTTCCGCCACCCCCACCCTGCCTAAACGCTCCCCA	XXUOXQXXQUXXIXTOXXOFXOOBIUXFXXSKLLH	NM											N
'''
# 00 FC30M30
# 01 111308
# 02 8
# 03 1
# 04 1183
# 05 1854
# 06 
# 07 2
# 08 ATTTATTTTCTCTATAAATAACCACTTTTATCTTT
# 09 XXXXXXXXXXXXX[E[RXXYXXXRXXXXXYCSSSS
# 10 mm_ref_chr6.fa
# 11 
# 12 133057049
# 13 R
# 14 14G15G4
# 15 12
# 16 0
# 17 
# 18 
# 19 -75
# 20 F
# 21 Y

def read_eland_export(f, seq2pos):
    for l in open(f):
        if l[0] == '#': continue
        fs = l[:-1].split('\t')
        if not fs[12]: continue
        seq, pos = fs[10], int(fs[12])
        if fs[13] =='R':
            pos += len(fs[8]) - pad # The index here was 1---a bug in the previous version?
            if pos < 1: pos = 1
        seq2pos.setdefault(seq, []).append(pos)
eland_formats.append((read_eland_export, '_export.txt'))

# eland_extended format.
extended_sample = '''\
>HWI-EAS276:1:2:4:1268#0/1	NCTTAGACANTTCTTCTGCCAGATATN	7:27:10	chr1.fa:104961443FG8T16C,191677418RG8T16C,chr12.fa:28414475FG8T16C,chr21.fa:19058017FG8T16C,chr3.fa:194596281FG8G16C,chr4.fa:27505258FC8T16C,chr7.fa:122845550FG8T16C
>HWI-EAS276:3:1:40:1070#0/1	GGCATTTTTTCAATTTGCTAGGAGCTC	0:1:1	chr1.fa:16722392R7A17C1,17086121F7A19
'''
# 0 >HWI-EAS276:1:2:4:1268#0/1
# 1 NCTTAGACANTTCTTCTGCCAGATATN
# 2 7:27:10
# 3 chr1.fa:104961443FG8T16C,191677418RG8T16C,chr12.fa:28414475FG8T16C,chr21.fa:19058017FG8T16C,chr3.fa:194596281FG8G16C,chr4.fa:27505258FC8T16C,chr7.fa:122845550FG8T16C

# Notes:
# 1) In field (3): G8T16C means the alignment looks like
# 'G--------T----------------C', where '-' means the corresponding NTs
# match.
#
# 2) For multiple locations, it appears that they are presented not in
# order of number of mismatches, but in order of position. Consider
# the second example above. Location (1, 16722392) has two mismatches,
# while (1, 17086121) has just one. What a pain.
mmire = re.compile(r'^>[^\t]+\t(?P<Read>[^\t]+)\t(?P<Single>1:0:0|0:1:0|0:0:1)?(?(Single)\t(?P<SeqId>[^:]+):(?P<Pos>\d+)(?P<Strand>[FR]).*|(?P<Multi>1:\d+:\d+|0:1:\d+)\t(?P<Locs>.+))\n')
locre = re.compile(r'((?P<SeqId>[^:,]+):)?(?P<Pos>\d+)(?P<Strand>[FR])(?P<Align>[^,]+),?')
alignre = re.compile(r'[^\d]?(?P<Idents>\d+)')
def read_eland_extended(f, seq2pos):
    for l in open(f):
        mmi = mmire.match(l)
        if not mmi: continue

        try:
            seqId, strand, pos = mmi.group('SeqId'), mmi.group('Strand'), int(mmi.group('Pos'))
        except TypeError:
            # look for best match based on align data.
            locs = mmi.group('Locs')
            best, seqId = [-1, '', '', -1], 'NoSeq'
            for locm in  locre.finditer(locs):
                newSeqId = locm.group('SeqId')
                if newSeqId: seqId = newSeqId

                idents = sum([int(alignm.group('Idents')) for alignm in alignre.finditer(locm.group('Align'))])
                if idents > best[0]: best = [idents, seqId, locm.group('Strand'), int(locm.group('Pos'))]
            dummy, seqId, strand, pos = best

        if strand =='R':
            pos += len(mmi.group('Read')) - pad # lot's of opportunities to be obo here.
            if pos < 1: pos = 1

        seq2pos.setdefault(seqId, []).append(pos)
eland_formats.append((read_eland_extended, '_eland_extended.txt'))
eland_formats.append((read_eland_extended, '_eland_multi.txt'))

# eland_result format.
result_sample = '''\
>HWI-EAS276:1:2:5:96#0/1	NGAAGAGCGNAAGTCCTTCTCAAAAAN	R2	0	0	3
>HWI-EAS276:1:2:4:366#0/1	NCTGAATATNAGCCTGAGTATCATACN	U1	0	1	0	chr8.fa	27691600	F	DD	12C
'''
# 0 >HWI-EAS276:1:2:4:366#0/1
# 1 NCTGAATATNAGCCTGAGTATCATACN
# 2 U1
# 3 0
# 4 1
# 5 0
# 6 chr8.fa
# 7 27691600
# 8 F
# 9 DD
# 10 12C

def read_eland_result(f, seq2pos):
    for l in open(f):
        if l[0] == '#': continue
        fs = l[:-1].split()
        if fs[2][0] == 'U':
            seq, pos = fs[6], int(fs[7])
            if fs[8] =='R':
                pos += len(fs[1]) - pad
                if pos < 1: pos = 1
            seq2pos.setdefault(seq, []).append(pos)
eland_formats.append((read_eland_result, '_eland_result.txt'))

# collate position data by sequence identifier
seq2pos = {}
for f in files:
    for rf, suffix in eland_formats:
        if f.endswith(suffix):
            sys.stderr.write('Using %s to read "%s" ...\n'%(rf.func_name, f))
            rf(f, seq2pos)
            break
    else:
        print >>sys.stderr, 'Skipping "%s": unrecogonized eland format.'%f

sys.stderr.write('... Done reading files.\n')

seqs = seq2pos.keys()
seqs.sort()

if wig:
    dumpDataFunc, genType = dumpWigData, "wiggle"
    sow('track type=wiggle_0\n')
else:
    dumpDataFunc, genType = dumpSgrData, "sequence graph"
    
sys.stderr.write('Generating %s data.\n'%genType)
for s in seqs:
    sys.stderr.write('Processing sequence %s ...\n'%s)

    ps = seq2pos[s]
    ps.sort()

    if stripSuffix:
        x = s.rfind('.')
        if x != -1: s = s[:x]

    # process data in groups defined by position gaps greater than pad.
    lx = 0
    for rx in xrange(1, len(ps)):
        if ps[rx-1]+pad < ps[rx]:
            dumpDataFunc(s, pad, lx, rx, ps)
            lx = rx
    dumpDataFunc(s, pad, lx, len(ps), ps)
