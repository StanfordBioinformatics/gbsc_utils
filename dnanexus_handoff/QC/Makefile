all: bwa_mismatches

bwa_mismatches: bwa_mismatches.c
	mkdir -p bin
	cc -o bin/bwa_mismatches -O2 -I$(SAMTOOLS_HOME)/include -L$(SAMTOOLS_HOME)/lib bwa_mismatches.c -lbam -lz
