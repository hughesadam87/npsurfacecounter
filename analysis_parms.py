''' Run parameters for imj analyis.  These parameters control various aspects
    of the individual run including whether or not to correct for np size 
    estimate, control imagej parms, size factors on protein counts etc...'''

size_parms={
           ### Adjust data to fit established np diameter
           'mean_correction':True,                     
           
           ### Use to scale limits of noise/flat/super regiosn in data
           
           'sing_low':None,  #Autofit
           'sing_high':None,      #Or a raw number like 60S

           ### Cannot be auto
           'flat_high':150.0,
           
           'scale_factor':1.0, #If you don't know what it is, leave at 1.    
           }

### ImageJ Parameters
imj_parms={
           'rsmall':0.0, 
           'rlarge':'Infinity', 
           'csmall':0.0, 
           'clarge':1.0, 
           'despeckle':True
           }

### Output and run-related parameters
run_parms={
       #   'basic_only':False, #If true, only do basic coverage analysis, else attempt advanced and default to basic        
          }

### Merge parameters
all_parms={'imj_parms':imj_parms, 'size_parms':size_parms, 'run_parms':run_parms}


