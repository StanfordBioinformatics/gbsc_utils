#!/bin/env python

from optparse import OptionParser

usage = "usage: %prog [options] SampleSheet.csv"
parser=OptionParser()

(opts, args) = parser.parse_args()
if not len(args)==1:
    parser.error('One input argument required')

input_file= args[0]
output_file='out.csv'

data_found = False
line = True
with open(input_file) as f:
    line = f.readline()
    while line:
        if line.startswith('[Data]'):
            data_found = True
            break
        line = f.readline()
    if data_found:
        f.readline() #Skip header
        with open(output_file,'w') as o:
            o.write(
                'FCID,Lane,SampleID,SampleRef,Index,Description,'+
                'Control,Recipe,Operator,Project\n')
            for line in f:
                parts = line.strip().split(',')
                if len(parts) != 11:
                    raise Exception('Wrong format. Expected 11 fields but got this: %s' % line)

                # Old format:
                fields = {}
                fields['Sample_ID'] = parts[0] 
                fields['Sample_Name'] = parts[1] 
                fields['Sample_Plate'] = parts[2] 
                fields['Sample_Well'] = parts[3] 
                fields['I7_Index_ID'] = parts[4] 
                fields['index'] = parts[5] 
                fields['I5_Index_ID'] = parts[6] 
                fields['index2'] = parts[7] 
                fields['Sample_Project'] = parts[8] 
                fields['Description'] = parts[9] 
                fields['GenomeFolder'] = parts[10] 

                new_index = fields['index']
                if fields['index2']:
                    new_index += '-' + fields['index2']

                #New format:

                new_fields = {}
                new_fields['FCID'] = ''
                new_fields['lane'] = '1'
                new_fields['sample_ID'] = fields['Sample_ID']
                new_fields['SampleRef'] = ''
                new_fields['Index'] = new_index
                new_fields['Description'] = fields['Description']
                new_fields['Control'] = ''
                new_fields['Recipe'] = ''
                new_fields['Operator'] = ''
                new_fields['Project'] = fields['GenomeFolder']

                o.write(
                ','.join(
                    [
                        new_fields['FCID'],
                        new_fields['lane'],
                        new_fields['sample_ID'],
                        new_fields['SampleRef'],
                        new_fields['Index'],
                        new_fields['Description'],
                        new_fields['Control'],
                        new_fields['Recipe'],
                        new_fields['Operator'],
                        new_fields['Project'],
                        ]
                    )
                +'\n'
                )
                
