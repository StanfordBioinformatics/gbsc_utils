from gbsc_utils.illumina import illumina_fastq_parse as illumina_fastq_parse
#from gbsc_utils.illumina import defunct as illumina_fastq_parse
import datetime

#Total number of lines in SCGPM_MD-DNA-1_HFTH3_L3_unmatched_R1.fastq is 347,060,820.
#log_fh = open("log_test_fastq_parse.txt","w")
#y = Illumina.FastqParse(fastq="/srv/gsfs0/projects/gbsc/workspace/nathankw/CIRM/CORN/SCGPM_MD-DNA-1_HFTH3_L3_unmatched_R1.fastq",log=log_fh)
#log_fh.close()


#illumina_fastq_parse.FastqParse(fastq="read_4mil.fq") #16 million lines
y = illumina_fastq_parse.FastqParse(fastq="read_25mil.fq") #100 million lines

#print(datetime.datetime.now())

