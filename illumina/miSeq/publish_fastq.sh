#!/bin/bash

src=$1
dest=$src/index.html

echo "<html>" >> $dest
echo "<head>" >> $dest
echo "<title>" >> $dest
echo "Unmapped reads for MiSeq run " $(basename $src) >> $dest
echo "</title>" >> $dest
echo "</head>" >> $dest
echo "<body>" >> $dest
echo "<h2>" >> $dest
echo "Unmapped reads for MiSeq run " $(basename $src) >> $dest
echo "</h2>" >> $dest
echo "<a href=\"SampleSheet.csv\">SampleSheet.csv</a><br/>" >> ${dest}
for fullname in ${src}/*.fastq*; do f=$(basename $fullname); echo "<a href=\"$f\">$f</a><br/>" >> ${dest}; done
echo "</body>" >> $dest
