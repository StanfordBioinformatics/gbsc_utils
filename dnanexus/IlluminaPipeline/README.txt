Mar. 12, 2014
Nathaniel Watson


convert_illumina_bcl.rb handles demultiplexing, as well as the samplesheet
generation.  For samplesheet generation, see method configure_samplesheet().


config.txt is an example configuration file for a run in our LIMS, which was
created with our query_lims.rb script.  The samplesheet code obtains parameters
from this config.txt file through a hash object.  The hash contains subhashes -
1 for each lane.
