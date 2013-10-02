from operator import attrgetter
from math import pi, sqrt
import os, shutil
import os.path as op

import logging
logger = logging.getLogger(__name__)

def logmkdir(fullpath):
    ''' Makes directory path/folder, and logs.'''
    logger.info('Making directory: "%s"' % fullpath)
    os.mkdir(fullpath)

def logwritefile(fullpath):
    ''' Open a file in 'w' mode; log that it has been opened. '''
    logger.info('Making writable outfile: "%s"' % fullpath)
    return open(fullpath, 'w')  #Note, user has to close

def get_shortname(filepath, cut_extension=False):
    ''' Return basename of filepath, with or without extension'''

    shortname=os.path.basename(filepath) 
    if cut_extension:
        shortname = op.splitext(shortname)[0]  #Cut file extension
    return shortname

def sort_summary(summary_file, delim='\t'):
    
    logger.info('Attempting to sort summary file: "%s"' % summary_file)
    f = open(summary_file, 'r')
    lines = f.readlines()
    lines = [line.strip().split(delim) for line in lines]
    header = lines.pop(0)
    f.close()

    ### Tries to sort by filenames then magnification of form 'f1_3000.tif'
    try:
        logger.info('Trying to sort by form: "f1_30000.tif"') #see images from (8/13/12)
        lines=sorted(lines, key=lambda item: (item[0].split('_')[0], int( item[0].split('_')[1].strip('.tif')) ) )
    except Exception:
        logger.info('Could not sort by7 form: "f1_3000.tif')

        ### Following exceptions are adhoc fixes for non-standard run names.
        firstname=lines[0][0].split('_')
        if 'f' in firstname[0] and 'b' in firstname[1]:
            try:
                logger.info('Trying to sort by form: "F1_b2_30kx"') #see images from (8/13/12)
                lines=sorted(lines, key=lambda item: (item[0].split('_')[1],(item[0].split('_')[0] ) ))
            except Exception:
                logger.info('Could not sort by form: "F1_b2_30kx"')

        ## Test for style ## 8_b2_f1_... (8/6/12)                        
        elif 'f' in firstname[2] and 'b' in firstname[1]:
            try:
                logger.info('Trying to sort by form: "8_b2_f1"')
                lines=sorted(lines, key=lambda item: (item[0].split('_')[1],(item[0].split('_')[2] ),(item[0].split('_')[3] ) ))
            except Exception:
                logger.info('Could not sort by form: "8_b2_f1"')

       ### TO ADD ###     
       ## Test for style ## 8_b2_f1_... (8/6/12) (test for 822)                       

    else:
        logger.info('Sorting successful, outputting summary.')
        f = logwritefile(summary_file, 'w')
        f.write(delim.join(header)+'\n\n')
        for i, line in enumerate(lines):
            ### Add a row divider between fibers
            if i > 0:
                if lines[i][0].split('_')[0] != lines[i-1][0].split('_')[0]:  #If switching fibers
                    f.write('\n')
                    
            f.write(delim.join(line) + '\n')

        f.close()

def get_files_in_dir(directory):
    ''' Given a directory, this returns just the files in said directory.  Surprisingly
        no one line solution exists in os that I can find '''
    
    files=[]
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            files.append(op.join(directory, item))
    return files

### The following methods navigate subdirectories and return file names in dictionaries ###

def magdict_foldersbymag(indir):
    ''' Makes a dictionary keyed by magnification of all files in subdirectories stored by magnification.
    Key=mag
    Value=Rootdirectory, [files]'''
    
    scaledict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
  #  outfiles=[(path+'/'+f) for f in files]
    for d in rootdirs:
        mag=d  #Value for magnification is in filename
        try:
            mag=int(mag)  #Raw magnification
        except ValueError:
            try:
                mag=int(mag.strip('k') )
                mag=mag*1000 #SCALE UP BY 1000            
            except ValueError:
                logger.error('failed to convert', d) 
            else:
                outfiles=get_files_in_dir(rootpath+'/'+d)
                scaledict[mag]=(d, tuple(outfiles) )
        else:
            outfiles=get_files_in_dir(rootpath+'/'+d)            
            scaledict[mag]=(d, tuple(outfiles) )
    return scaledict

def magdict_foldersbyrun(indir):
    ''' Makes a dictionary keyed by magnification of all files in subdirectories stored by run.
    This function, unlike scaledict, will exam all folders in the indirectory, but only can
    keep files if they have a magnifciation in their name with underscore delimiters.  Returns
    any files that were not understood.
    Key=mag
    Value=Rootdirectory, [files]'''
    
    raise NotImplementedError('This function is broken, really it is tough to return key by'
    'mag because of how directory is structured.  Makes for sense to just use rundict_foldersbyrun'
    'and modify main_script.py to make right outdir')
  
    filedict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    warnings=[] #Stores names of files that could not be 
    for folder in rootdirs:
        all_files=get_files_in_dir(rootpath+'/'+folder) #list of lists (files per folder)           
        for afile in all_files:
            shortname=get_shortname(afile, cut_extension=True)
            sfile=shortname.split('_')  #Will not error even if no underscore
            mag=[]  #Store magnification of file
            for piece in sfile:
                try:
                    number=int(piece)
                except ValueError:
                    pass
                else:
                    mag.append(number)
            if len(mag) != 1:
                warnings.append(get_shortname(afile, cut_extension=False))
            else:
                mag=mag[0]
                if mag not in filedict.keys():
                    filedict[mag]=[]
                for entry in filedict[mag]:
                    if not entry:  #If list is empty
                        filedict[mag].append([folder, [] ])
                filedict[mag].insert(0, [folder, [] ] )
                filedict[mag][0][1].append(afile)
    warnings='\t'.join(warnings)
    return filedict, warnings


def rundict_foldersbyrun(indir):
    ''' Takes in folders by run and keys dictionary by folder name.  Values are 
    magnification to filename pairs.  If magnification can't be determined from
    filename, warnings will track it.
    
    Key=Rootdirectory
    Value=mag, [files]'''
    filedict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    all_files=[get_files_in_dir(rootpath+'/'+d) for d in rootdirs] #list of lists (files per folder)   
    warnings=[] #Stores names of files that could not be 
    for folder in rootdirs:
        filedict[folder]=[]
        for afile in get_files_in_dir(rootpath + '/'+d):
            shortname=get_shortname(afile, cut_extension=True)
            sfile=shortname.split('_')  #Will not error even if no underscore
            mag=[]  #Store magnification of file
            for piece in sfile:
                try:
                    number=int(piece)
                except ValueError:
                    pass
                else:
                    mag.append(number)
            if len(mag) != 1:
                warnings.append(get_shortname(afile, cut_extension=False))
            else:
                mag=mag[0]
                filedict[folder].append( (mag, afile) )
    warnings='\t'.join(warnings)
    return filedict, warnings    

                
        
        #mag=d  #Value for magnification is in filename
        #try:
            #mag=int(mag)  #Raw magnification
        #except:
            #ValueError
            #try:
                #mag=int(mag.strip('k') )
                #mag=mag*1000 #SCALE UP BY 1000            
            #except:
                #ValueError
                #print 'failed to convert', d
            #else:
                #outfiles=get_files_in_dir(rootpath+'/'+d)
                #scaledict[mag]=(d, tuple(outfiles) )
        #else:
            #outfiles=get_files_in_dir(rootpath+'/'+d)            
            #scaledict[mag]=(d, tuple(outfiles) )
    #return scaledict    


def add_keylist(indic, key, val):
    ''' Adds value to dictionary.  If key found, appends or ovewrites based
        on truth value of append.'''
    
    if isinstance(val, float):
        val=round(val, 2)

    if key in indic:
        indic[key].append(val)
    else:
        indic[key]=[val]
    return indic    

def test_suite_lowcoverage(imbuster, indic=None):
    '''Test developed on 4/8/13 to output various quanties of interest in
       trying to assess accuracy in low coverage fibers.  Probes quantitie like
       circularity of just the single particles in the distribution bounds and 
       area of particles in the distribution.
       
       indic= Dictinoary to accumulate results over several runs.'''
    if not indic: indic={}
    add_keylist(indic, 'Image', imbuster.shortname)
    xmin,xmax=imbuster.fit_min_max
    xmean=imbuster.fit_mean
    
    add_keylist(indic, 'fit_start', xmin)
    add_keylist(indic, 'fit_mean', xmean)
    add_keylist(indic, 'fit_end', xmax)
    
    ### Take all single data
    singles=imbuster.single_particles
    circ=imbuster._quick_frame(singles, 'circ')
    singlearea=imbuster._quick_frame(singles, 'area')
    total_count=len(imbuster.count_results)
    samparea=imbuster.sampled_area
    
    ### Scale singles up to total equivalence if covered whole area with just singles
    scaleup=int(round(imbuster.total_sensing_area / imbuster.sampled_area,0)) 
    
    add_keylist(indic, 'Total particles', scaleup*total_count)
    add_keylist(indic, 'Single particles', scaleup*len(singles))
    add_keylist(indic, 'Single circularity', imbuster.mean_bin_circ)
    
    add_keylist(indic, 'Analyze Particles error', imbuster.particle_fitting_error)
    
    ### Correct singles area for diameter transformation
    singles_area=(100.0*singlearea.sum() / samparea)
    add_keylist(indic, 'Coverage from singles(uncorrected)', singles_area)
       
    ### Scale the predicted coverage (from particle sum, but could be from BW) by a correction factor
    if imbuster.mean_corrected_coverage:
        correction=imbuster._area_correct(imbuster.uncorrected_dmean, xmean)
        correctedarea=correction * singles_area   
        add_keylist(indic, 'Coverage from singles (corrected)', correctedarea)
        add_keylist(indic, 'Uncorrected histmean', imbuster.uncorrected_dmean)

        ### Look at mean from area transformed.
        amean=sqrt( (4.0 * singlearea.mean()) / pi)
        add_keylist(indic, 'Uncorrected data mean', amean)
        add_keylist(indic, 'Guassian fit error', 100.0* (amean - imbuster.uncorrected_dmean )/ amean)
        
    
    return indic

def output_testsuite(indic, outfile, delim='\t'):
    ''' Outputs the dictionary of test_suite_lowcoverage into an outfile.'''

    ordering=['Image', 'Total particles', 'Single circularity',
              'Single particles', 'Coverage from singles(uncorrected)',
              'Coverage from singles (corrected)', 'Uncorrected histmean', 'Uncorrected data mean',
              'Analyze Particles error', 'Guassian fit error',  'fit_start', 'fit_mean', 'fit_end']
    o=open(outfile, 'w')
    for k in ordering:
        o.write(k + delim + delim.join([str(i) for i in indic[k]]) + '\n\n')
    
    o.close()  
              
def make_root_dir(rootout, overwrite=False):
    ''' Creates directory structure for program results output.  Warning, if overwriting, all files and subfolders
        in the root out directory will be destroyed, not just ones pertaining to the relevant infiles.'''
    ### Check if outdirectory already exists and react decide to overwrite or error ###
    if os.path.exists(rootout):
        if overwrite:
            print 'Deleting directory and all contents of, %s' %rootout
            shutil.rmtree(rootout)
        else:
            raise IOError('Directory %s already exists, remove or set overwrite to True'%rootout)
        
    ### Make output directory and subdirectories ###    
    print 'making directory %s' %rootout
    os.makedirs(rootout)


### Deprecated functions below ###
def out_getter(imjobject, with_header=True, delim='\t'):
    ''' This is a special getter which takes in attribute fields as well as corresponding mapping functions
    to format return in a sexy way.  Couldn't quite rig it up properly so this is not in use!'''

    empty=lambda x: x #How to handle null case
    fround=lambda x: round(x, 2) #Quick rounding
  #  scaleout='%s/pixel'%units, round(scale,3) #NEED TO MAKE UNITS AN ATTRIBUTE GETTER!!!
    join_it=lambda x: delim.join([str(item) for item in x])
    
    outparms=[('shortname',empty), ('af_coverage',fround), ('bw_coverage', fround,), ('diam_min_mode_max', join_it), \
              ('percent_sampled',fround), ('scale',fround),('field_of_view', join_it,)]
    
    outfields=[item[0] for item in outparms]
    f=attrgetter(*outfields)    
    atts=f(imjobject)
    outstring=''
    if with_header:
        outstring=outstring+'#'+(delim.join(outfields))+'\n'
        
#    for i, item in enumerate(outparms):
 #       outstring=outstring+delim+str(item[1](atts[i]))
        
    outstring=outstring+delim.join(str(item[1](atts[i])) for i,item in enumerate(outparms) )+'\n'
        
    return outstring
    