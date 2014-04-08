/*
 * bwa_mismatches.c
 * 
 * Generate statistics about mismatching positions in a SAM/BAM file
 * produced by the BWA aligner.
 *
 * Phil Lacroute
 */

#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include <malloc.h>
#include <assert.h>
#include "bam/sam.h"

extern char *optarg;

static struct option long_opts[] = {
    {"out", required_argument, 0, 'o'},
    {"sam_in", no_argument, 0, 'S'},
    {"verbose", no_argument, 0, 'v'},
    {0, 0, 0, 0}
};

static char *short_opts = "o:Sv";

void
usage(int exit_code)
{
    fprintf(stderr,
	    "Usage: bwa_mismatches [options] file ...\n"
	    "Options:\n"
	    "  -o, --out file         data output file\n"
	    "  -S, --sam_in           input is SAM (default BAM)\n"
	    "  -v, --verbose          print verbose messages\n");
    exit(exit_code);
}

void
check_read_length(unsigned qlen, unsigned *read_len,
		  unsigned **read_error_count)
{
    if (*read_len == 0) {
	*read_len = qlen;
	*read_error_count = (unsigned *)malloc(sizeof(unsigned) * qlen);
	memset(*read_error_count, 0, sizeof(unsigned) * qlen);
    } else if (*read_len != qlen) {
	fprintf(stderr, "bam_mismatches: reads have different lengths\n");
	exit(1);
    }
}

void print_mismatches(FILE *fp, unsigned read_len, unsigned *read_error_count,
		      unsigned analyzed_count)
{
    unsigned cycle;

    for (cycle = 0; cycle < read_len; ++cycle) {
	double frac;
	if (analyzed_count == 0) {
	    frac = 0;
	} else {
	    frac = (double)read_error_count[cycle] / (double)analyzed_count;
	}
	fprintf(fp, "%.4f %u\n", frac, read_error_count[cycle]);
    }
}

int
main(int argc, char **argv)
{
    char *out_file = 0;
    int sam_in = 0;
    int verbose = 0;

    int opt;
    int paired = -1;
    unsigned total_count = 0;
    unsigned analyzed_count = 0;
    unsigned read1_len = 0;
    unsigned read2_len = 0;
    unsigned *read1_error_count = 0;
    unsigned *read2_error_count = 0;
    FILE *out_fp;

    if (argc <= 1) {
	usage(0);
    }

    /* parse command-line options */
    while ((opt = getopt_long(argc, argv, short_opts, long_opts, 0)) >= 0) {
	switch (opt) {
	case 'o':
	    out_file = optarg;
	    break;
	case 'S':
	    sam_in = 1;
	    break;
	case 'v':
	    verbose = 1;
	    break;
	default:
	    usage(1);
	    break;
	}
    }

    if (optind + 1 > argc) {
	usage(1);
    }

    if (out_file == 0) {
	out_fp = stdout;
    } else if ((out_fp = fopen(out_file, "w")) == NULL) {
	fprintf(stderr, "bwa_mismatches: cannot open output file %s\n",
		out_file);
	return 1;
    }

    for (; optind < argc; ++optind) {
	char *infile = argv[optind];
	char *infile_mode;
	samfile_t *in;
	bam1_t *abuf;

	if (verbose) {
	    printf("Scanning %s...\n", infile);
	}

	/* open input file */
	if (sam_in) {
	    infile_mode = "r";
	} else {
	    infile_mode = "rb";
	}
	in = samopen(infile, infile_mode, 0);
	if (in == 0) {
	    fprintf(stderr, "bwa_mismatches: cannot open input file %s\n",
		    infile);
	    return 1;
	}
    
	/* scan the input file */
	abuf = bam_init1();
	while (samread(in, abuf) > 0) {
	    const bam1_core_t *acore = &abuf->core;
	    unsigned read_len = 0;
	    unsigned *read_error_count = 0;
	    int num_pos, mismatches, gaps;

	    ++total_count;

	    /* check read length and paired/single flags */
	    if (acore->flag & BAM_FPAIRED) {
		if (paired < 0) {
		    paired = 1;
		} else if (!paired) {
		    fprintf(stderr, "bwa_mismatches: found both paired and "
			    "single reads\n");
		    return 1;
		}
		if (acore->flag & BAM_FREAD1) {
		    check_read_length(acore->l_qseq, &read1_len,
				      &read1_error_count);
		    read_len = read1_len;
		    read_error_count = read1_error_count;
		} else if (acore->flag & BAM_FREAD2) {
		    check_read_length(acore->l_qseq, &read2_len,
				      &read2_error_count);
		    read_len = read2_len;
		    read_error_count = read2_error_count;
		} else {
		    fprintf(stderr, "bwa_mismatches: found paired-end "
			    "read without read number\n");
		    return 1;
		}
	    } else {
		if (paired < 0) {
		    paired = 0;
		} else if (paired) {
		    fprintf(stderr, "bwa_mismatches: found both paired and "
			    "single reads\n");
		    return 1;
		}
		check_read_length(acore->l_qseq, &read1_len,
				  &read1_error_count);
		read_len = read1_len;
		read_error_count = read1_error_count;
	    }

	    if (acore->flag & BAM_FUNMAP || acore->tid < 0) {
		/* read was not aligned */
		continue;
	    }

	    /* the read was aligned; check if it meets the criteria */
	    num_pos = bam_aux2i(bam_aux_get(abuf, "X0"));
	    mismatches = bam_aux2i(bam_aux_get(abuf, "XM"));
	    gaps = bam_aux2i(bam_aux_get(abuf, "XO"));

	    if (num_pos != 1) {
		/* read maps to multiple locations */
		continue;
	    }
	    if (gaps != 0) {
		/* alignment has gaps */
		continue;
	    }

	    /* the read meets all criteria; now find the mismatches */
	    ++analyzed_count;
	    char *md_cigar = bam_aux2Z(bam_aux_get(abuf, "MD"));
	    int cycle = 0;
	    char *mdc;
	    for (mdc = md_cigar; *mdc; ) {
		assert(cycle < read_len);
		if (isdigit(*mdc)) {
		    cycle += strtoul(mdc, &mdc, 10);
		} else if (index("ACGTN", *mdc) != 0) {
		    ++read_error_count[cycle];
		    ++mdc;
		} else {
		    fprintf(stderr, "bwa_mismatches: unexpected character "
			    "'%c' in MD cigar\n", *mdc);
		    return 1;
		}
	    }
	}
	bam_destroy1(abuf);
	samclose(in);
    }
    if (verbose) {
	printf("Processed %u out of %u reads.\n",
	       analyzed_count, total_count);
	if (paired > 0) {
	    printf("Paired reads, %u bases + %u bases\n",
		   read1_len, read2_len);
	} else {
	    printf("Single reads, %u bases\n", read1_len);
	}
    }

    /* print data */
    fprintf(out_fp, "mmfraction mmcount\n");
    print_mismatches(out_fp, read1_len, read1_error_count, analyzed_count);
    if (paired > 0) {
	print_mismatches(out_fp, read2_len, read2_error_count,
			 analyzed_count);
    }
    if (out_file != 0) {
	fclose(out_fp);
    }

    return 0;
}
