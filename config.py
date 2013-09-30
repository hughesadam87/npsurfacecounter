''' Set of commands to control path lookup and other hackey user-dependent quantities.
Although this doesn't solve the problem, at least I won't have to alter source code and 
instead can adjust all variables here.'''

import sys

#################
### CHANGE ME ###
#################
selected='adam_lab'

# Set of possible computers to choose from.  Labpc2 is evelyn's main station next to adam's lab computer and
# also desktop by printer.
selections=['adam_lab', 'adam_home', 'labpc']

if selected not in selections:
    raise AttributeError('%s must be one of the following:"%s"'%(selected, ','.join(selections)))
                
     
### Path to pyrecords on each machine           
pyrec_path={'adam_lab':'/home/glue/Dropbox/pyrecords', 
            'adam_home': '/home/hugadams/Dropbox/pyrecords', 
            'labpc':'/home/reeves/Dropbox/pyrecords'}

sys.path.append(pyrec_path[selected])

### import pyrecord stuff
from Utilities.utils import from_file, to_dataframe, to_dic #From pyrecords
from Utilities.utils import histogram as hcount #To avoid namespace conflicts
from Core.immutablemanager import ImmutableManager


### ImageJ path
imj_path={'adam_lab':'/home/glue/Desktop/ImageJ/jre/bin/java -Xmx512m -jar /home/glue/Desktop/ImageJ/ij.jar',    
'adam_home':'/home/hugadams/Desktop/ImageJ/jre/bin/java -Xmx512m -jar /home/hugadams/Desktop/ImageJ/ij.jar',    
'labpc':'/home/reeves/Desktop/ImageJ/jre/bin/java -Xmx512m -jar /home/reeves/Desktop/ImageJ/ij.jar'}  

path_to_imagej=imj_path[selected]


