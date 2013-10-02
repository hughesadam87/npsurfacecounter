import os, sys, shutil

###Pyrecords imports
from imjfields import ij_manager, results_manager, grey_manager
from config import from_file, to_dic #From pyrecords

###Local module imports
from imk_utils import get_shortname, get_files_in_dir, magdict_foldersbymag, make_root_dir, \
     sort_summary, rundict_foldersbyrun
from imk_class import ImageDestroyer
from man_adjust import manual_adjustments
from scipy import integrate
from imk_utils import test_suite_lowcoverage, output_testsuite

## Histogram plot parameters
from histogram_params import size_hists, grey_hissy, circ_hissy

def main_go(indir, outdir, all_parms, compact_results=True):   
    ''' Script to take a batch of SEM images and perform customized imagej and python-based analysis'''
    
    imj_parms, size_parms, run_parms=all_parms['imj_parms'], all_parms['size_parms'],\
                        all_parms['run_parms']
    
    ### Store internal file parameters in dictionary keyed by magnifications
    indict=magdict_foldersbymag(indir)  #Folders arranged by magnification, keyed by magnification
    
    ### If I use these methods below, have to change script below because 
    #indict, warning=rundict_foldersbyrun(indir)  #Arranged by run, keyed by run  

    testdic={} #For 4/8/guassian testing

    ### Output main output root directory. 
    make_root_dir(outdir, overwrite=True)  ## BE VERY CAREFUL WITH THIS

    ### Perpare run-summary files ###
    summary_filename=outdir+'/'+'full_summary.xls'
    light_summary_filename=outdir+'/'+'light_summary.xls'
    coverage_summary=outdir+'/'+'detailed_summary.xls'
    out_delim='\t' 
    full_summary=open(summary_filename, 'w')
    light_summary=open(light_summary_filename, 'w')
    cov_summ=open(coverage_summary, 'w')
    
    ### Prepare log-files to alert user of warnings, especially missing adjustments###
    logfilename=outdir+'/'+'MISSING_ADJUSTMENTS.txt'
    errorfilename=outdir+'/'+'RUN ERRORS'
    logfile=None ; errorfile=open(errorfilename, 'w')  

    ### OUTPUT FOR LOW COVERAGE TESTING ON 4/8/13
    apriltest=outdir+'/'+'april_TEST.txt'


    ### Output run parameters but can't use shutil
    parmsout=open(outdir+'/'+'Run Parameters', 'w')
    parmsout.write('ImageJ Parameters:\n\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in imj_parms.items()) )
    parmsout.write('\n\nSize Parameters:\n')
    parmsout.write( ('\t').join((str(k)+'\t'+str(v) ) for k,v in size_parms.items()) )
    parmsout.close()
    
    
    ### Setup the subdirectories by magnification
    filecount=0
    for mag,(direc, infiles_full) in indict.items():
        rootpath=outdir+'/'+direc
        os.mkdir(rootpath) #Make subdirectory    

    ### Iterate through file-by-file
        for infile in infiles_full:
            infile_shortname=get_shortname(infile, cut_extension=False) 
            outpath=rootpath+'/'+get_shortname(infile, cut_extension=True) #Cut extension is here
            os.mkdir(outpath)
            
            try:
                adjust, crop, npmean=manual_adjustments[infile_shortname]  #This is important          
            except KeyError:
                adjust=None ; crop=None ; npmean=None  #adjust=None means manual adjustments used
                if not logfile:
                    logfile=open(logfilename, 'w')
                    logfile.write('##### MISSING ADJUSTMENTS AND/OR NPSIZE ######')
                logfile.write('\n'+infile_shortname)
                
            ### Instantiate the ImageJ analysis class ###
            imbuster=ImageDestroyer(infile, mag, outpath, adjust=adjust, crop=crop, particle_parms=imj_parms)    
            print 'Analyzing image %s' %infile
             
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
                    logfile.write('\n'+'NPSIZE MISSING FOR INFILE %s.  Cannot\
                      perform size analysis'%infile)
                else:          
                    npmean=float(npmean)
                    
                    ### Reset the data based on the scaled_data_from_hist
                    imbuster.scale_data_from_hist(npmean, special_outname='D_scaled')

            

#            imbuster.hist_and_bestfit(attstyle='area', special_outname='area_dist')      
                                                                                 
            ### ADVANCED COVERAGE ANALYSIS       
            imbuster.coverage_analysis_advanced(flat_high=float(size_parms['flat_high']), single_low=size_parms['sing_low'],
                                                    single_high=size_parms['sing_high'], super_adj_style='hemisphere', super_fill_in_cracks=False)


            try:
            
                #imbuster.hist_and_bestfit(attstyle='length', smart_bin_range=(26.5, 65.0))  #Store an internal histogram/best fit represntation of length
                
                
           ### Make a scatter matrix of important columns
       #         imbuster.scatter_matrix(['length', 'circ'])
                
                   
           ### Plot the image adjustment threshold histogram ###
                print 'Making greyscale histograms'
                imbuster.greyscale_hist(**grey_hissy)
                
                                 
           ### Make histograms.  Sometimes is best to leave this as an exception as various parameters 
           ### of histograms can cause errors.
                                     
                ### Circularity histogram
                print 'Making particle analysis histogram for circularity'            
                if compact_results:
                    hdir=outpath+'/'+'Histogram_circ'
                    os.mkdir(hdir)  #DOES THIS OUTPUT 
                else:
                    hdir=None                
                imbuster.super_histogram('circ', special_outpath=hdir, shadeattr='mode', lineattr=None, **circ_hissy)                
                                                                                                                         
                ### Size Histograms for particle analysis ###          
                histtypes=['psuedo_d','area']#, 'diameter]
                lineatts=['feret']#, 'mode', 'mean','solidity']
                for htype in histtypes:
                    print 'Making particle analysis histogram for %s'%htype
                    
                    if compact_results:
                        hdir=outpath+'/'+'Histograms_'+htype
                        os.mkdir(hdir)  #DOES THIS OUTPUT 
                    else:
                        hdir=None
                    
                    for histsize in size_hists: #Iterate over length ranges       
                        imbuster.digiframe._set_binnumber_from_data_binwidth('length', 0.5*imbuster.min_pixel_length)                             
                        for att in lineatts:
                            if htype == 'area' and histsize['outname']=='mid-range':  #Quick hack to get nice area histogram w/o changing how this works.
                                    histsize['lengthrange']=(0.0,8000.) #Area hack            
                                    histsize['color']='red'
                            imbuster.super_histogram(htype, shadeattr=None, colorattr=None, lineattr=att, mapx=None, \
                                                 special_outpath=hdir, **histsize)
            except Exception as e:
                errorfile.write('\n%s found in file %s \n'%(str(type(e)),infile))
                errorfile.write(str(e))
                                    
                                    
            ### April 4/8/13 Coverage tests
            testdic=test_suite_lowcoverage(imbuster, testdic)
            
        
            ### Output individual quicksummary file ###
            imbuster.full_summary()
            
            ## Add results to the run summary file ##
            if filecount == 0:
                sum_out=imbuster.special_summary(delim=out_delim, with_header=True, style='full') 
                lite_out=imbuster.special_summary(delim=out_delim, with_header=True, style='lite')     
                cov_out=imbuster.special_summary(delim=out_delim, with_header=True, style='detailed')              
  
            else:
                sum_out=imbuster.special_summary(delim=out_delim, with_header=False, style='full')
                lite_out=imbuster.special_summary(delim=out_delim, with_header=False,style='lite')                       
                cov_out=imbuster.special_summary(delim=out_delim, with_header=False, style='detailed')     

                
            full_summary.write(sum_out)
            light_summary.write(lite_out)
            cov_summ.write(cov_out)
            
            filecount+=1
            
            
    ### April 4/8/13 Coverage tests            
#    output_testsuite(testdic, apriltest)
                    
            
    ### Close files ###
    full_summary.close() ;  light_summary.close() ; cov_summ.close() 
    if logfile:
        logfile.close()
    if errorfile:
        errorfile.close()

    ### Sort output, specify alternative file extensions
    out_exts=['.txt']
    outsums=[summary_filename, light_summary_filename, coverage_summary]
    
    for sumfile in outsums:
        sort_summary(sumfile, delim=out_delim)  #Pass filenames not 
        for ext in out_exts:
            shutil.copyfile(sumfile, sumfile.split('.')[0] + ext)
    #sort_summary(light_summary_filename, delim=out_delim)
    #sort_summary(coverage_summary, delim=out_delim)

    
                
            
### MAIN PROGRAM ###
if __name__ == '__main__':	
    
    from analysis_parms import all_parms    

    
    #Avoid ./ notation, it will confuse output scripts/macros
    wd=os.getcwd()
    basedir=wd+'/testdata'  
   # basedir=wd+'/Data'
    baseout=wd+'/RunResults'
    
    walker=os.walk(basedir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    for folder in rootdirs:    
           
        indir=rootpath+'/'+folder
        outdir=baseout+'/'+folder
        main_go(indir, outdir, all_parms)#, dmean)


