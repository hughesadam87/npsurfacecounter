import os, sys, shutil
import os.path as op

###Pyrecords imports
from imjfields import ij_manager, results_manager, grey_manager
from config import from_file, to_dic #From pyrecords

import logging
logger = logging.getLogger(__name__)
from logger import logclass, configure_logger

###Local module imports
from imk_utils import get_shortname, get_files_in_dir, magdict_foldersbymag, make_root_dir, \
     sort_summary, rundict_foldersbyrun
from imk_class import ImageDestroyer
from man_adjust import manual_adjustments
from scipy import integrate
from imk_utils import test_suite_lowcoverage, output_testsuite, logwritefile, logmkdir

## Histogram plot parameters
from histogram_params import size_hists, grey_hissy, circ_hissy

OUT_DELIM = '\t'  #Used in many outfiles; don't recall how pervasive
    

def main(indir, outdir, all_parms, compact_results = True):   
    ''' Script to take a batch of SEM images and perform customized imagej and 
    python-based analysis.  Mostly wraps imk_class.py.
    
    all_parms: 
       Dictionary of supplied parameters including imj_parms, size_parms, run_parms
       
    compatc_results:
       If true, I belive it attempts to change output directory structure.  
       Leave as is (10/2/13) until a future refactor.
       
    NOTES:
      There is a rundict_foldersbyrun method, but it's commented out.  Expects
      folders ordered by mag of strict structure:
              InRoot --- RUnname --- mag --- images
        eg:
              RunData --- 3_3_13 --- 30000 --- f1.tif
              
        Walker needs refactored to alleviate this, or at least raise an error
        when this format is not used.'''
    
    imj_parms, size_parms, run_parms = \
        all_parms['imj_parms'], all_parms['size_parms'], all_parms['run_parms']
    
    ### Store internal file parameters in dictionary keyed by magnifications
    logger.info('Attempting to read folders arranged by magnification.')
    indict = magdict_foldersbymag(indir)  #Folders arranged by magnification, keyed by magnification
    logger.debug('indict is: %s' % indict)
    
    ### If I use these methods below, have to change script below because 
    #indict, warning=rundict_foldersbyrun(indir)  #Arranged by run, keyed by run  

    #testdic = {} #For 4/8/guassian testing

    ### Output main output root directory. 
    logger.warn('Making outdirectory IN OVERWIRTE MODE: "%s"' % outdir)
    make_root_dir(outdir, overwrite=True)  ## BE VERY CAREFUL WITH THIS

    ### Perpare run-summary files ### (used in sorting at end of script, so don't remove yet)
    summary_filename = op.join(outdir, 'full_summary.xls')
    light_summary_filename = op.join(outdir, 'light_summary.xls')
    coverage_summary = op.join(outdir+'detailed_summary.xls')
    
    full_summary = logwritefile(summary_filename)
    light_summary = logwritefile(light_summary_filename)
    cov_summ = logwritefile(coverage_summary)
    
    ### OUTPUT FOR LOW COVERAGE TESTING ON 4/8/13
#    apriltest = op.join(outdir, 'april_TEST.txt')

    ### Output run parameters but can't use shutil
    parmsout= logwritefile(op.join(outdir, 'Run Parameters'))
    parmsout.write('ImageJ Parameters:\n\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in imj_parms.items()) )
    parmsout.write('\n\nSize Parameters:\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in size_parms.items()) )
    parmsout.close()
    
    ### Setup the subdirectories by magnification
    filecount=0
    for mag,(direc, infiles_full) in indict.items():
        rootpath=op.join(outdir, direc)
        logmkdir(rootpath) #Make subdirectory    

    ### Iterate through file-by-file
        for infile in infiles_full:
            infile_shortname = get_shortname(infile, cut_extension=False) 
            outpath = op.join(rootpath, get_shortname(infile, cut_extension=True)) #Cut extension is here
            logmkdir(outpath)
            
            try:
                adjust, crop, npmean=manual_adjustments[infile_shortname]  #This is important          
            except KeyError:
                adjust=None ; crop=None ; npmean=None  #adjust=None means manual adjustments used
                logger.warn('Manual adjustment settings NOT FOUND for %s' % infile)
                
            ### Instantiate the ImageJ analysis class ###
            imbuster=ImageDestroyer(infile, mag, outpath, adjust=adjust, crop=crop, particle_parms=imj_parms)    
            logger.info('Analyzing image %s' % infile)
             
            #### Make and run imagej macro        
            imbuster.make_imjmacro()
            imbuster.run_macro()
            imbuster.initialize_count_parameters() #Store results in dataframe objects
            
            ### FIT A GUASSIAN IF POSSIBLE.  Also plots by default
            imbuster.hist_and_bestfit(attstyle='psuedo_d', special_outname='D_distribution') #smart_bin_range=(30.0,70.0))  #Store an internal histogram/best fit represntation of length             
              
            #########################
            ## Particle sizing ######
            #########################  
              
            ### Set mean particle size to user-specified value from npparms 
            if size_parms['mean_correction']:
                if not npmean:
                    logger.info('NPSIZE MISSING FOR INFILE %s.  Cannot'
                      ' perform size analysis' % infile)
                else:          
                    npmean=float(npmean)
                    ### Reset the data based on the scaled_data_from_hist
                    imbuster.scale_data_from_hist(npmean, special_outname = 'D_scaled')
                    logger.info('NPMEAN is: %s.  Data has been rescaled' % npmean)

#            imbuster.hist_and_bestfit(attstyle='area', special_outname='area_dist')      
                                                                                 
            ### ADVANCED COVERAGE ANALYSIS       
            logger.info('Running coverage analysis')
            imbuster.coverage_analysis_advanced(flat_high=float(size_parms['flat_high']), single_low=size_parms['sing_low'],
                                                    single_high=size_parms['sing_high'], super_adj_style='hemisphere', super_fill_in_cracks=False)
            logger.info('Coverage analysis completed')


            try:
            
                logger.info('Entering various histogram phases of main()')
                #imbuster.hist_and_bestfit(attstyle='length', smart_bin_range=(26.5, 65.0))  #Store an internal histogram/best fit represntation of length
                
                
           ### Make a scatter matrix of important columns
       #         imbuster.scatter_matrix(['length', 'circ'])
                
                   
           ### Plot the image adjustment threshold histogram ###
                logger.info('Making greyscale histograms')
                imbuster.greyscale_hist(**grey_hissy)
                
                                 
           ### HISTOGRAM-RELATED STUFF.  Sometimes is best to leave this as an exception as various parameters 
           ### of histograms can cause errors.
                                     
                ### Circularity histogram
                logger.info('Making particle analysis histogram for circularity')
                if compact_results:
                    hdir=op.join(outpath, 'Histogram_circ')
                    logmkdir(hdir)  
                else:
                    hdir = None                
                imbuster.super_histogram('circ', special_outpath=hdir, shadeattr='mode', lineattr=None, **circ_hissy)                
                                                                                                                         
                ### Size Histograms for particle analysis ###          
                histtypes = ['psuedo_d','area']#, 'diameter]
                lineatts = ['feret']#, 'mode', 'mean','solidity']
                for htype in histtypes:
                    logger.info('Making particle analysis histogram for %s' % htype)
                    
                    if compact_results:
                        hdir = op.join(outpath, htype)
                        logmkdir(hdir)  #DOES THIS OUTPUT 
                    else:
                        hdir=None
                    
                    for histsize in size_hists: #Iterate over length ranges       
                        imbuster.digiframe._set_binnumber_from_data_binwidth('length', 0.5*imbuster.min_pixel_length)                             
                        for att in lineatts:
                            #Quick hack to get nice area histogram w/o changing how this works.
                            if htype == 'area' and histsize['outname'] == 'mid-range':  
                                    histsize['lengthrange']=(0.0,8000.) #Area hack            
                                    histsize['color']='red'
                            imbuster.super_histogram(htype, shadeattr=None, colorattr=None, lineattr=att, mapx=None, \
                                                 special_outpath=hdir, **histsize)
            except Exception as e:
                logger.critical('Histogram analysis failed.  Returned error:\n%s' % e)
                                    
            ### April 4/8/13 Coverage tests
     #       logger.warn('Running adhoc method "test_suite_lowcoverage" from 4/8 testing.')
     #       testdic = test_suite_lowcoverage(imbuster, testdic)            
        
            ### Output individual quicksummary file ###
            imbuster.full_summary()
            
            ## Add results to the run summary file ##
            if filecount == 0:
                sum_out = imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='full') 
                lite_out = imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='lite')     
                cov_out = imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='detailed')              
  
            else:
                sum_out = imbuster.special_summary(delim=OUT_DELIM, with_header=False, style='full')
                lite_out = imbuster.special_summary(delim=OUT_DELIM, with_header=False,style='lite')                       
                cov_out = imbuster.special_summary(delim=OUT_DELIM, with_header=False, style='detailed')     

                
            full_summary.write(sum_out)
            light_summary.write(lite_out)
            cov_summ.write(cov_out)
            
            filecount+=1
            
            
    ### April 4/8/13 Coverage tests            
#    output_testsuite(testdic, apriltest)
                    
            
    ### Close files ###
    full_summary.close() ;  light_summary.close() ; cov_summ.close() 

    ### Sort output, specify alternative file extensions
    out_exts=['.txt']
    outsums=[summary_filename, light_summary_filename, coverage_summary]
    
    for sumfile in outsums:
        logger.info("Attempting sort summary.") #what's this doing?
        sort_summary(sumfile, delim=OUT_DELIM)  #Pass filenames not 
        for ext in out_exts:
            shutil.copyfile(sumfile, sumfile.split('.')[0] + ext)
    #sort_summary(light_summary_filename, delim=OUT_DELIM)
    #sort_summary(coverage_summary, delim=OUT_DELIM)

    
                
            
### MAIN PROGRAM ###
if __name__ == '__main__':	
    
    from analysis_parms import all_parms    

    configure_logger(screen_level='debug', name=__name__)
    
    #Avoid ./ notation, it will confuse output scripts/macros
    inroot = op.abspath('testdata')
    outroot = op.abspath('RunResults')
    
    walker=os.walk(inroot, topdown=True, onerror=None, followlinks=False)
 
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    for folder in rootdirs:    
            
        indir = op.join(rootpath, folder)
        outdir = op.join(outroot, folder)
        
        logger.info( 'Analyzing folder: "%s"' % folder )
        logger.debug( 'Analysis parms are: %s' % all_parms )
        main(indir, outdir, all_parms)


