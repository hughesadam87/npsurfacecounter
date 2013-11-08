import os, sys, shutil
import os.path as op
from scipy import integrate


###Pyrecords imports
from imjfields import ij_manager, results_manager, grey_manager
from config import from_file, to_dic #From pyrecords
from models import TexModel

import logging
logger = logging.getLogger(__name__)
from logger import logclass, configure_logger, LogExit

###Local module imports
from imk_class import ImageDestroyer
from man_adjust import manual_adjustments
from imk_utils import get_shortname, get_files_in_dir, magdict_foldersbymag, make_root_dir, \
     sort_summary, rundict_foldersbyrun, to_histsummary, to_textable, test_suite_lowcoverage, \
     output_testsuite, logwritefile, logmkdir, tif_to_png, tex_preview


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
    
    tex_images = {} #10/23 dictionary to store histograms for putting into reports
    
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
    coverage_summary = op.join(outdir, 'detailed_summary.xls')
    
    _lite1=''
    _lite2=''
    
    full_summary = logwritefile(summary_filename)
    light_summary = logwritefile(light_summary_filename)
    cov_summ = logwritefile(coverage_summary)
    
    ### Output run parameters but can't use shutil
    parmsout= logwritefile(op.join(outdir, 'Run Parameters'))
    parmsout.write('ImageJ Parameters:\n\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in imj_parms.items()) )
    parmsout.write('\n\nSize Parameters:\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in size_parms.items()) )
    parmsout.close()

    ### Check to see if folder is in manual_adjustments
    if op.basename(indir) in manual_adjustments: 
        adjust_dic = manual_adjustments[op.basename(indir)]
        logger.info('Manual adjustments folder found for %s' % op.basename(indir))
    else:        
        logger.critical('Manual adjustments NOT FOUND FOR ENTIRE DIRECTORY "%s"'
                        % op.basename(indir))    
        adjust_dic = {}  #So a key error is raised below
        
        # Each file itself if not found will raise an additional warning
    
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
                adjust, crop, npmean = adjust_dic[infile_shortname]          
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
            logger.info("Particle stats imported: found %s uncorrected particles." % len(imbuster.areas))
            
            # Store attributes for tex summary
            texmodel = TexModel()
            
            texmodel.adjust = adjust
            # Make a png version of image or cropped image
            croppedfile = op.join(outpath, op.splitext(infile_shortname)[0]+'_cropped.tif')
            if op.exists(croppedfile):
                texmodel.image_path = tif_to_png(croppedfile, outpath)
            else:
                texmodel.image_path = tif_to_png(infile, outpath)
                
            adj_path = op.join(outpath, op.splitext(infile_shortname)[0]+'_adjusted.tif')
            texmodel.adjust_path = tif_to_png(adj_path, outpath)
            
            texmodel.bright_path = op.join(outpath, 'Brightness_distribution.png')             
            texmodel.folder = op.basename(indir)
            
            ### FIT A GUASSIAN IF POSSIBLE.  Also plots by default

            histpath=imbuster.hist_and_bestfit(attstyle='psuedo_d', special_outname='D_distribution') #smart_bin_range=(30.0,70.0))  #Store an internal histogram/best fit represntation of length             
            texmodel.hist_path1 = histpath.split(outroot)[-1] #Add histogram for report
                   
            #########################
            ## Particle sizing ######
            #########################  
              
            ### Set mean particle size to user-specified value from npparms 
            if size_parms['mean_correction']:
                if not npmean:
                    logger.info('NPSIZE MISSING FOR INFILE %s.  Cannot'
                      ' perform size analysis' % infile)
                else:          
                    npmean = float(npmean)
                    ### Reset the data based on the scaled_data_from_hist
                    histpath=imbuster.scale_data_from_hist(npmean, special_outname = 'D_scaled')
                    texmodel.hist_path2 = histpath.split(outroot)[-1] #Add histogram for report

                    logger.info('NPMEAN is: %s.  Data has been rescaled' % npmean)

#            imbuster.hist_and_bestfit(attstyle='area', special_outname='area_dist')      
                                                                                 
            ### ADVANCED COVERAGE ANALYSIS       
            logger.info('Running coverage analysis')
            try:
                imbuster.coverage_analysis_advanced(flat_high=float(size_parms['flat_high']), single_low=size_parms['sing_low'],
                                                    single_high=size_parms['sing_high'], super_adj_style='hemisphere', super_fill_in_cracks=False)
            except (Exception, LogExit) as Exc:
                logger.critical('%s FAILURE: coverage analysis:\n%s' %(infile_shortname, Exc))
                continue
                                                
                
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
            except (Exception, LogExit) as e:
                logger.critical('%s FAILURE: Histogram analysis:\n%s' %(infile_shortname, e))
                continue                
            ### April 4/8/13 Coverage tests
     #       logger.warn('Running adhoc method "test_suite_lowcoverage" from 4/8 testing.')
     #       testdic = test_suite_lowcoverage(imbuster, testdic)           
     
            texmodel.set_from_imbuster(imbuster)
        
            #Add texmodel to dictionary
            tex_images[infile_shortname]= texmodel
        
            ### Output individual quicksummary file ###
            imbuster.full_summary()
            
            ## Add results to the run summary file ##
            if filecount == 0:
                sum_out = imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='full') 
                _lite1 += imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='lite')
                _lite2 += imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='lite_part_2')
                cov_out = imbuster.special_summary(delim=OUT_DELIM, with_header=True, style='detailed')              
  
            else:
                sum_out = imbuster.special_summary(delim=OUT_DELIM, with_header=False, style='full')
                _lite1 += imbuster.special_summary(delim=OUT_DELIM, with_header=False,style='lite')
                _lite2 += imbuster.special_summary(delim=OUT_DELIM, with_header=False, style='lite_part_2')          
                cov_out = imbuster.special_summary(delim=OUT_DELIM, with_header=False, style='detailed')     

                
            full_summary.write(sum_out)
            cov_summ.write(cov_out)
            
            filecount+=1
            

    light_summary.write(_lite1 +'\n\n' + _lite2)            
                                
    ### Close files ###
    full_summary.close() ;  light_summary.close() ; cov_summ.close()

    # Make .tex file for light summary
    logger.info("Created latex summarytable")
    summarytablepath = op.join(outdir,'summarytable.tex')
    
    with open(summarytablepath, 'w') as o:        
        try:
            for idx, sumfile in enumerate([_lite1, _lite2]):
                if idx == 0:
                    head = op.basename(indir)
                else:
                    head = ''
                textable = to_textable(sumfile, head=head)
                o.write(textable) 
                o.write('\n\n')
        except (Exception, LogExit) as exc:
            logger.critical('Texorate FAILED: %s' % sumfile)
            print exc #Why aint trace working?  Cuz of how i'm catching these?
    
    logger.info("Creating latex histtable") #what's this doing?     
    histtablepath = op.join(outdir, 'histsummary.tex')
    with open(histtablepath, 'w') as o:
        try:
            o.write(to_histsummary(tex_images))
            o.close()
        except (Exception, LogExit) as exc:
            logger.critical('Texfigure FAILED: %s' % sumfile)
            print exc #Why aint trace working?  Cuz of how i'm catching these?
            
    previewpath = op.join(outdir, op.basename(indir)+'_preview.tex')
    with open(previewpath, 'w') as o:
        o.write( tex_preview(summarytablepath, histtablepath) )
    logger.info("Compiling preview.tex")
       
    ### Sort .xls files output, specify alternative file extensions
    out_ext = '.txt'
    outsums=[summary_filename, coverage_summary]    
    
    logger.info("Attempting sort summary.")        
    for sumfile in outsums:
        try:        
            sort_summary(sumfile, delim=OUT_DELIM)  #Pass filenames not 
            shutil.copyfile(sumfile, sumfile.split('.')[0] + out_ext)

        except (Exception, LogExit) as e:
            logger.warn('%s sort summary failed!' % sumfile )  

    # Handle light summary specially
    shutil.copyfile(light_summary_filename, light_summary_filename.split('.')[0] + out_ext)

          

    # Compile tex code
    logger.info("Compiling preview.tex")
    wd = os.getcwd()
    os.chdir(outdir)
    os.system('textopdf %s' % previewpath)
    os.chdir(wd)

            
### MAIN PROGRAM ###
if __name__ == '__main__':	
    
    from analysis_parms import all_parms  

    #Avoid relative paths, it will confuse output scripts/macros
    inroot = op.abspath('testdata')
    outroot = op.abspath('RunResults')
    logfile=op.join(outroot, 'runlog.txt')
    
    #Haven't included anything special for debuging; need argparse/CLI
    if '-v' in sys.argv:
        configure_logger(screen_level='info', logfile=logfile, 
                         name=__name__)
    else:
        configure_logger(screen_level='warning',logfile=logfile,
                         name=__name__)
    
    walker=os.walk(inroot, topdown=True, onerror=None, followlinks=False)
 
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles) = walker.next()
    # Error if directories are empty
    if not rootdirs: 
        logger.error("VALID DIRECTORY STURCTURE MUST BE: RUN --> MAG --> IMAGES")

    for folder in rootdirs:                
        
        indir = op.join(rootpath, folder)
        outdir = op.join(outroot, folder)
        
        logger.info( 'Analyzing folder: "%s"' % folder )
        logger.debug( 'Analysis parms are: %s' % all_parms )

        main(indir, outdir, all_parms)

    # Run pyclean
    os.system('pyclean .')

