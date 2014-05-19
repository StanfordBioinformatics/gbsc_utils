echo 'Running '$(basename $0)' ...'
tmp=tmp
infile=${tmp}/in.fastq
mkdir -p $tmp
cat <<EOF > $infile
@MONK:315:C2PWKACXX:6:1101:1458:1967 1:N:0:CGTACTAGTAGCCCGC
TCTGACCGGTGACGCCCTGTTCAGCTTGCGCTGCGATTGTGGCTTCCAGCTCGAAGCGGCANTGACGCAAATTGCCGNGN
NANNNCGGNNNATNNTGCTGT
+
CCCFFFFFHHHGHIJJJIJJJGIJIJIIIJEHJJJBHHIGII@CG=A=CAHFFBCC@BB88#,,28<;39;>@@######
#####################
@MONK:315:C2PWKACXX:6:1101:1430:1973 1:N:0:CGTACTAGTAGTTCGC
CTATTAGCTTTTGGCTGTAGATATGCTTGCTATCAAGTCAAGTATGTTTCGCTATTTTTGAAATTTATTTTAAAAAATAN
NTNNAAAANNNCANNGTCTAT
+
CCCFFFFFHHHHHJJJJJJJJJJJJJJJJJJJJJJJJIIJJJFDDGGIJIJJJJJJJJJIIJJIJJJJJJJJIHGGFFF#
#####################
@MONK:315:C2PWKACXX:6:1101:1412:1998 1:N:0:CGTACTAGTAGATCCC
CTTCTGACCCGTCTTAGCTCTCCGTTGTCATCATCGAACACTCATTTGATTCCTTCTTCAGCTGCTTTCCAATAGAAAAN
NAAGATTTNNNATNNCAAGGC
+
@@@DDDDDDHHFFBDC?CB>BFEBFHFEHHDB@DFEHG3?D3B?FHIIBHGI@@DHFGC>FHGCGC:@@EIEEEE@ABB#
#####################
@MONK:315:C2PWKACXX:6:1101:1484:1998 1:N:0:CGTACTAGTTGTTCGC
TTGCTGATGATTCGCGTCGAGGCGCTTGAGTCTGAAGCTTTGGAAGTTTCGGTTGTTGCATCTCTACTTTTGAGATACTN
NTGATGTTNCNGTNTTGGTCT
+
CCCFFFFFHHHHHJJJIJJJJJIJJJJJGIGGIJHIIIJJJJIDHHCHHGFFDDDDDBCDEDDDEEDEDEDC?BB@CDC#
#+28?BDC#+#++#+8<B@CC
EOF

../extract_barcodes.sh $infile
result=$(cat ${infile}.barcodes)
expected=$(cat <<EOF
CGTACTAGTAGCCCGC
CGTACTAGTAGTTCGC
CGTACTAGTAGATCCC
CGTACTAGTTGTTCGC
EOF
)
if [ "$result" != "$expected" ]
    then
    echo "... FAILED. Expected '$expected'"
    echo "but instead found '$result'"
    else
    rm -r $tmp
    echo "... PASSED"
fi
