#-------------------------------------------------------------------------------
# Name: ImageDestroyer
# Purpose: Perform particle analysis on batches of images through Python and ImageJ
# Author: Adam Hughes
# Created: 22/09/2012
# Python Version: EPD 7.3
#-------------------------------------------------------------------------------

import shutil, sys, subprocess, os, itertools
import os.path as op
from math import pi, sqrt
from copy import deepcopy
from operator import itemgetter

import logging
logger = logging.getLogger(__name__)
from logger import logclass

### 3rd party modules imports ###
import numpy as np
from PIL import Image
from pandas import DataFrame, Series
from pandas.tools.plotting import scatter_matrix
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.integrate import simps


### Local module imports ###
from imk_utils import get_shortname
from imjfields import ij_manager, results_manager, grey_manager
from digitizer import MultiHistMaster, df_rebin, get_bin_points,\
     optimize_gaussian, fit_normal, psuedo_symmetric, hist_max,\
     data_from_histogram, get_binwidth, digitize_by, gauss, range_slice,\
     bin_above_below

from BSA_plots import bsa_count
from statsmodels.stats import diagnostic
#from cachedprop import cached_property  #Busted for now

from config import from_file, to_dataframe, path_to_imagej #From pyrecords
from config import hcount #To avoid namespace conflicts

#r2=lambda x: str(round(x,2))

def r2(x):
    if x is None:  
        return 'None'
    return str(round(x,2))
    
def roundint(x):
    ''' Round to whole float and then take int'''
    return int(round(x,0))

@logclass(log_name=__name__ , public_lvl='info',
          #skip=['_ts_from_picklefiles', 'from_namespace'])
          )
class ImageDestroyer(object):
    ''' Class used to do various imagej analysis things in python'''

    ### Class attributes have the same value no matter what image is being analyzed. ###
    UNITS = 'nm'  
    RCORE = 31250.0   #Optical fiber diameter is 62.5 so radius is 31.25um

    @property
    def total_sensing_area(self):
        '''Defines the area of the sampled surface'''
        return pi * self.RCORE**2  #units**2

    @total_sensing_area.setter
    def total_sensing_area(self):
        self.RCORE=sqrt(self.total_sensing_area / pi)


    @property
    def mag_scale(self):
        ''' This is a scaling between magnification and pixel units.  Inherently based on 1024*768 resolution image.
        If a higher/lower res image is passed in, this will be adjusted in the _set_image_parameters() method.'''
        if self.UNITS == 'um':
            logger.critical('UNITS set to "um", but these have not been thoroughly tested.'
                            ' "nm" are strongly recommended".')
            return 0.00277 #um/pixel

        elif self.UNITS == 'nm':
            return 2.777   #nm/pixel based on 100k mag and 1024*768 image. Annie showed equivalence/linearity at all scales    

    ### These are the variables that change with each image.  Called "Instance variables" ###   
    def __init__(self, image, mag, outpath, adjust=None, crop=None, particle_parms=None):
        '''
        Parameters:
        --------------
           particle_parms: ImageJ related parameters as dictionary 
           (despeckle=True, rs=0.0, rl=Infinity etc...)
           
        '''        
        self.image=image
        self.mag=mag
        self.outpath=outpath

        ### User-supplied image adjustment parameters
        self.adjust=adjust  #User-supplied manual threshold 
        self.crop=crop      #User-supplied cropping dimensions
        self.particle_parms=particle_parms #Parameters passed to imagej to analyze particles

        ### Store filenames that will be populated by imagej macro.  
        ### Put them in here just for convienence, incase need to access easily later
        self.results_file= self.circles_file= self.thresh_file= self.cropped_file= \
            self.greyscale_file= self.bw_file= self.macrofile=None

        self.digiframe=None #Attribute stores special histogram data operations


        ### Optimized guassian to length histogram fit
        self.mpx_critical=6.0 #nm (This is min pixel length threshold required before attempting \
        #to curve fit a histogram with an optimized gaussian.  Could still use manual guassian at coarse
        #resolutions.  5.9 is for 50k at low res!

        ### Internal Histogram attributes
        self.histogram = None
        self._binnumber = 37  #Used internally for histogram.  Chosen aesthetically
        ### Forced-thresholding correction parameters
        self.uncorrected_dmean = None

        ### Gaussian autofit attributes (self.best_fit stored functional representation of guassian)
        self.fit_amp = self.fit_mean = self.fit_attribute = self.fit_sig = None
        self.idxhismax = self.xhismax = self.yhismax = None

        self.about_zero=0.2 #Lower lim on fit function where it's regarded as 0
        self.hist_inc=100.0 #Number of increments between mean and sigma used when iterating on histogram

        # Particle counting attributes
        self.noise_particles = self.single_particles=self.flat_particle_equiv = self.super_particle_equiv=None      
        self.flat_particle_actual = self.super_particle_actual = None
        
        # Particle area attributes
        self.noisy_area = self.singles_area = self.doubles_area = \
            self.flats_area = self.supers_area = None
        
        # BSA Attributes
        self.bsa_from_singles = self.bsa_from_flats = self.bsa_from_supers = None
        self.bsa_parms_numbers = self.bsa_parms_attstyle=self.bsa_cov_style = None        
        self.bsa_countstyle='dual'

        ###Doubles are only returned if coverage_analysis_advanced is used, so if these are 0, it doens't mean 
        ###There aren't really doubles, but only that method can even return them!
        self.double_particle_equiv=self.bsa_from_doubles=0  


        ### Output summary file
        self.summary_out="%s/%s_quickresults.txt" %(self.outpath, get_shortname(self.image, cut_extension=True))  

        ### Set a variety of attributes from parameters in the image ###
        self.resolution, self.min_pixel_length, self.picture_area=self._set_image_parameters(self.image)

        ### Initialize private variabels for properties that have setters
        self._length_bin_width=self.min_pixel_length
        self._area_bin_width=self.min_pixel_area

    ### Property attributes (useful when attributes require a function to be calculated). 
    ### Quite useful when setting attribute values is not trivial like x.b=5

    ### File properties ###
    @property
    def shortname(self):
        '''Shortname of infile'''
        return get_shortname(self.image, cut_extension=False)     

    @property
    def shortname_noext(self):
        '''Shortname of infile without extension'''
        return get_shortname(self.image, cut_extension=True)     

    ### Coverage and counting properties ###
    @property
    def field_of_view(self):
        ''' Determines the length dimensions of fiber sampled- chooses depending on if cropped picture. 
        Careful, must be called after croppedfile has been accessed to it will default to full image'''
        if self.cropped_file:
            pic_pixels=self._set_image_parameters(self.cropped_file)[0]
        else:
            pic_pixels=self.resolution
        return (pic_pixels[0]*self.min_pixel_length, pic_pixels[1]*self.min_pixel_length)         

    @property
    def sampled_area(self):
        ''' Determines the area of fiber sampled'''
        return float(self.field_of_view[0] * self.field_of_view[1]) #Float for later division useage
    
    @property
    def single_counts(self):
        try:
            return len(self.single_particles) #To avoid truth testing array
        except TypeError:
            return None

    @property
    def min_pixel_area(self):
        ''' Min area in a pixel (scale does all the work, this is just scale **2)'''
        return self.min_pixel_length**2  

    @property
    def percent_sampled(self):
        ''' Percent of total surface area sampled in image'''
        return 100.0 * (self.sampled_area / self.total_sensing_area)

    ### Bestfit/guassian and histogram related properties
    @property
    def bincenters(self):
        if not self.histogram:
            return None        
        return get_bin_points(self.histogram[1], position='c')
    
    @property
    def binlefts(self):
        if not self.histogram:
            return None        
        return get_bin_points(self.histogram[1], position='l')
    
    @property
    def binrights(self):
        if not self.histogram:
            return None        
        return get_bin_points(self.histogram[1], position='r')    

    @property
    def best_fit(self):
        ''' Returns a gaussian function generator based on internally stored optimized curve.'''
        if self.fit_amp:
            return lambda x: self.fit_amp*np.exp(-(x-self.fit_mean)**2/(2.*self.fit_sig**2))
        else:
            return None
        
    @property
    def dx(self):
        '''Computes increment for iterating over best fit from specified # increments in 
        self.hist_inc and standard devation of histogram.  For example, user can set 100
        points between mean and first standard deviation as a way of defining resolution of
        any histogram, despite attribute style.'''
        return self.fit_sig / float(self.hist_inc)
    
    @property
    def mean_bin_circ(self):
        ''' Computes the circularity at the fit mean or bin mean with +/-
            10% left right weighting.  Uses real data. Useful for determing
            circularity around single particles region.'''

        width=0.1 #10%
        if self.fit_mean:
            mean=self.fit_mean
        else:
            mean=self.xhismax
            
        xmin,xmax=(1.0-width)*self.fit_mean , (1.0+width)*self.fit_mean       
        ds=self._quick_slice((xmin,xmax), 'psuedo_d')
        circ=self._quick_frame(ds, 'circ')            
        return circ.mean()

        
    @property
    def fit_min_max(self):
        ''' Returns min/max bounds of the histogram where it essentially gets close enough to 0.
            This min criteria is stored in self.about_zero.  Does this by iterating stepwise
            in increments determined by self.hist_inc and the value of standard devation.
            Should be attribute independent as it relies on self.fit_attributes and sigma'''
        
        #Early return None
        if not self.fit_amp:
            return (None, None)

        f=self.best_fit #For convience rereference function
       
        ### Set start, end and increment for iterating over fit fcn
        dmax=self.count_results[self.fit_attribute].max()
        dmin=self.count_results[self.fit_attribute].min()
        
        ### Set starting values for x and y
        xmin=xmax=self.fit_mean
        y=f(self.fit_mean)
        
        ### Iterate from mean to x=dmax
        while y > self.about_zero:
            xmax=xmax+self.dx
            y=f(xmax)
            
            if xmax > dmax:
                xmax=None
                break

        y=f(self.fit_mean)
            
        ### Iterate from mean to x=dmin
        while y > self.about_zero:
            xmin=xmin-self.dx
            y=f(xmin)
            
            if xmin < dmin:
                xmin=None
                break
        
        return (xmin, xmax)
                
    ### Verified that this was equal to
    @property
    def fit_area(self):
        ''' Computes the area of the fitting guassian function.  Note this
            is in xunits, and not the total diameter of all the particles 
            in a histogram.  See below method'''
        if not self.fit_amp:
            return None
        return self.fit_amp  * abs(self.fit_sig) * sqrt(2.0*pi) 
     
        
    ### WHY IS THIS NEGATIVE
    @property
    def fit_cumulative_area(self):
        ''' Computes Int( x f(x) ) numerically for all points on the guassian.
            Gives a truer estimate of the net diamter or area or w/e for all
            particles under the curve.  Should be close to the sum of bins.'''

        if not self.fit_amp:
            return None

        xs,xf=self.fit_min_max
        x=np.arange(xs, xf, self.dx) #or go only half way, eg to mean?
        y=x * self.best_fit(x)
        return simps(x,y)        
        
    @property
    def fwhm(self):
        ''' Full width at half max of guassian.  Width is independent of 
            amplitude determined completely by sigma up to an arbitrary 
            translation of fit mean.  Returns x,y of point right of mean.'''
        if self.fit_amp:
            x=self.fit_mean + (2.3548200 * self.fit_sig)
            return (x, self.best_fit(x))
        else:
            return None
        
            

    @property
    def bw_coverage(self):
        ''' Computes particle coverage based on bw image file.'''
        bw_counts=[stat.count for stat in self.bw_results]        
        bw_white, bw_black = (float(bw_counts[0]), float(bw_counts[-1]) )
        return 100.0 * ( bw_black/ (bw_black + bw_white) )    
    
    @property
    def imjpart_coverage(self):
        ''' Computes the coverage based on total area of the particles after
            imageJ has fit a border to them in analyze particles.  Does not
            remove NOISE particles, or depend on particle equivalents (eg doubles, mids).'''
        
        area=self.count_results['area'].sum()
        return 100.0 * (area/self.sampled_area)
    

    @property
    def noisy_coverage(self):
        ''' Coverage due to particles under a certain size restriction.  Set in bsa_count_coverage()'''
        return (self.noisy_area/self.sampled_area) * 100.0

    @property
    def noiseless_bw_coverage(self):
        ''' Takes blackwhite imjg coverage and corrects for noise.  Noise
            set in coverage_analysis_advanced()'''
        return self.bw_coverage - self.noisy_coverage        
    
    @property
    def particle_fitting_error(self):
        ''' This computes the ratio of the blackwhite coverage
	to that of the imagej coverage cutting noise out of both estimates.'''
        ### noiseless particle coverages
         # pandas 0.12 way...
#        partcover = 100.0 * (self.count_results['area'][self.singles_low::].sum() / self.sampled_area)
 
        # pandas 0.14 way
        area = self.count_results['area']	
        partcover = 100.0 * (area[area >= self.singles_low].sum() / self.sampled_area)
        bw = self.noiseless_bw_coverage
        return 100.0 * ((bw - partcover) / bw)
    
    
    def _area_correct(self, dold, dnew):
        '''Given we make the transformation d -> d', computes an area scale factor
           assuming a circular particle. For example, d goes from 10-15, this the
           change in area of circular particles with these diameters.  
           
           kwds:
              dold/dnew- old and new desired mean diameters 
           
           returns: scale factor (eg 1.05 or .98).  User should then scale surface
           coverage by this factor.
           '''
        
        e=0.5 * ( dnew - dold )
        amean_old=0.25 * pi * dold**2
        gamma= pi  * ( dold*e + e**2)  #Worth storing for use in testing        
        return (1.0+ gamma/amean_old)
    
    @property
    def mean_corrected_coverage(self):
        ''' Take bw coverage MINUS NOISE and scales it if user supplied a forced-threshloding change.
            Performs the simple transformation A(d) --> A(d + e).'''
        
        if self.uncorrected_dmean:
            d = self.uncorrected_dmean
            coverage = self.noiseless_bw_coverage
            
            if self.fit_mean:
                dnew = self.fit_mean
            else:
                dnew = self.xhismax
                
            scale = self._area_correct(d, dnew) 
            return self.noiseless_bw_coverage * scale
        
        else:
            return None

    @property
    def doubles_range(self):
        ''' Stores range that allows for doubles.  By default, particle mean
        up to flat low.  Counting methods will know how to bisect the regions of
        fit appropriately.  Without fit, doubles can't be computed.'''
        if self.fit_mean:
            return (self.fit_mean, 2.0*self.fit_mean)
        else:
            return None
        
    @property
    def mpx_crit_met(self):
        '''Tracks if the current image has small enough pixel resolution to warrant size analysis. '''
        if self.min_pixel_length <= self.mpx_critical:
            return True
        else:
            return False

    @property
    def crude_total_nps(self):
        '''Scales field of view NPS to total surface area.  Counts each aggreagate as a nanoparticle,
        and possibly single pixels as particle meaning it is grossly misestimates actual NP count.'''        
        nps=len(self.lengths)
        return roundint(float(nps) * self.total_sensing_area / self.sampled_area  ) 

    @property
    def _np_total_equiv_withnoise(self):
        '''Nanoparticle estimation BEFORE throwing out lower/noise estimate JUST FOR THE FIBER IMAGE, not scaled
        to full fiber. Only really useful for summary stuff.'''
        return self.noise_particles+ self.single_counts + self.flat_particle_equiv\
                 + self.double_particle_equiv+self.super_particle_equiv        
    
    @property
    def _np_total_equiv_nonoise(self):
        '''Nanoparticle estimation AFTER throwing out lower/noise estimate JUST FOR THE FIBER IMAGE, not scaled
        to full fiber. Only really useful for summary stuff.
           - Float returned since these are almost always used in quotients in outputs.'''
        return float( self.single_counts + self.flat_particle_equiv  
                 + self.double_particle_equiv+self.super_particle_equiv )


    @property
    def _np_total_actual_withnoise(self):
        '''Nanoparticle estimation BEFORE throwing out lower/noise estimate JUST FOR THE FIBER IMAGE, not scaled
        to full fiber. Only really useful for summary stuff.'''
        return float( self.noise_particles + self.single_counts + self.flat_particle_actual 
                 + self.double_particle_actual + self.super_particle_actual )

    @property
    def _np_total_actual_nonoise(self):
        '''Nanoparticle estimation BEFORE throwing out lower/noise estimate JUST FOR THE FIBER IMAGE, not scaled
        to full fiber. Only really useful for summary stuff.'''
        return float( self.single_counts + self.flat_particle_actual 
                 + self.double_particle_actual + self.super_particle_actual )


    @property
    def double_particle_actual(self):
        if self.double_particle_equiv:
            return roundint(0.5 * self.double_particle_equiv)

    ### Total NP Count estimations below
    @property
    def np_total_corrected(self):
        '''Nanoparticle estimation after throwing out lower/noise estimate, then decomposing aggregates.'''
        return roundint( 
                   (self.total_sensing_area / self.sampled_area ) * self._np_total_equiv_nonoise   
                   )
    
    ### Actual imagej particle estimation, not equivalent breakdown.  Should be same as imj particle analysis- noise
    @property
    def true_particles_total_nonoise(self):
        '''Essentially how many imagej particles were found minus noise.  Breakdown if wondering "ok how many
        super aggregates"'''
        return roundint(
                  (self.total_sensing_area / self.sampled_area ) * \
                   (self.single_counts + self.flat_particle_actual + \
                    self.super_particle_actual + self.double_particle_actual ) 
                        )

    # FILL FRACTION
    @property
    def packing_area(self):
        ''' Added 11/2/13:  Divides the area consumed by singles, doubles and flats by the 
            total area of the image MINUS the noise/super particles.  Effectively, cuts out
            supers and noise, and asks, what percentage is full.  This is the basis for
            determination of fill fraction.'''
        
        area_nosupers = self.sampled_area - (self.supers_area + self.noisy_area)
        return (self.singles_area + self.doubles_area + self.flats_area) / area_nosupers
    
    @property
    def fillfrac_hexagonal(self):
        ''' If assume hexagonal packing, maximum area that can be filled is 90.9%. 
            This just takes packing area divides by 90.9%.  See "circle packing
              Remember, SUPERS and NOISE already removed '''

        return self.packing_area / .9069
    
    @property
    def fillfrac_square(self):
        ''' If assume square packing, max area fillable is 0.78598 (pi/4 ).
              Remember, SUPERS and NOISE already removed '''

        return self.packing_area / 0.78539


    # BSA PROPERTIES
    @property
    def _bsa_proportion(self):
        ''' All bsa on image, scaled up to fiber dimensions.  Important for summary.'''
        return (self.bsa_from_flats+ self.bsa_from_doubles+ self.bsa_from_singles+self.bsa_from_supers)
    
    @property
    def bsa_total(self):
        ''' All proteins on np's'''
        return roundint((self.total_sensing_area / self.sampled_area) * self._bsa_proportion)
                   

    ### ImageJ output properties 
    ### Chose to transform outfiles into these properties for easy access,
    ### aesthetics and so they aren't created until accessed

    ### Once built, setters of bin_number/width will trigger updates but changing
    ### restults file for example will not change this.  Made to work with only
    ### one set of results.
    @property
    def count_results(self):
        '''Stores particle count stats from imagej output file in memory using PyRecords.  
        On first call, it will instantiate the dataframe in the digitizer class.  I actually
        add a computed attribute length to the digiframe because it is so useful.'''
        if not self.digiframe:
            self.initialize_count_parameters()        
        return self.digiframe.df

    #@cached_property     
    @property
    def grey_results(self):
        '''Stores black white pixel count stats from imagej output file in memory using PyRecords'''
        return from_file(grey_manager, self.greyscale_file, parsecomments=True)    

    #@cached_property 
    @property
    def bw_results(self):
        return from_file(grey_manager, self.bw_file, parsecomments=True) 

    ### Statistics of most interest get their own attributes for easy access later  
    #@cached_property     
    @property
    def areas(self):
        '''Stores particle areas from count_results.  Merely for convienence since so used.'''
        return self.count_results.area

    @property
    def lengths(self):
        '''Stores particle length from count_results.  Merely for convienence since so used.'''
        return self.count_results.length        

    ### MIN MODE MAX VALUES FROM DATASET (min not from theoretical pixel minimum) ###

    @property
    def area_min_mode_max(self):  
        ''' Tuple of min, mode, max of diameters.  Could do this for areas too if desirable'''
        return self.digiframe.min_mode_max('area')


    @property
    def length_min_mode_max(self): 
        ''' Tuple of min, mode, max of diameters.  Could do this for areas too if desirable.  
        Note, most likely will return single-pixel value or something, so need other methods
        to actually specify filters (eg d>10).'''
        return self.digiframe.min_mode_max('length')

    ### Next groupings of parameters are used in summary methods.  Having them as attributes,
    ### lets me call them from several summary files.
    @property
    def input_parms(self):
        return(('despeckle', self.particle_parms['despeckle']) ,
               ('crop', self.crop), 
               ('thresholding', self.adjust))     

    @property    
    def sample_parms(self):
        return (('% Surface sampled',  r2(self.percent_sampled)), #Total fiber core area
                ('Area Sampled', str(round(self.sampled_area,0))))

    @property
    def coverage_parms(self):
        return (('bw_noisy(%)', r2(self.bw_coverage)),
                ('part_cover(%)',r2(self.imjpart_coverage)),
                ('bw_nonoise(%)',r2(self.noiseless_bw_coverage)),
                ('anal_part_error',r2(self.particle_fitting_error)),
                ('noise_cover(%)', r2(self.noisy_coverage)),                
                ('corr_cov(%)',r2(self.mean_corrected_coverage)),)

    @property
    def image_parms(self):
        return (
            ('Filename', self.shortname),
            ('magnification', self.mag),
            ('field of view(%s)'%self.UNITS, \
             (round(self.resolution[0]*self.min_pixel_length , 0) ,\
              round(self.resolution[1]*self.min_pixel_length , 0) ) ),
            ('resolution', self.resolution),  
            ('%s/pixel'%self.UNITS, r2(self.min_pixel_length)))


    @property
    def particle_analysis_parms(self):
        ''' Particle analysis full detail '''        
        return(
            
        ('IMJ particles (no noise)', self.true_particles_total_nonoise),  
        ('nanoparticles', self.np_total_corrected),   

        ### Particle breakdown ###
        ('noise_particles', self.noise_particles),
        ('singles',self.single_counts),
        ('doubles_equiv', self.double_particle_equiv),
        ('mids_equiv',self.flat_particle_equiv),
        ('bigs_equiv',self.super_particle_equiv),     
        ('doubles_actual', self.double_particle_actual),
        ('mids_actual',self.flat_particle_actual),
        ('bigs_actual', self.super_particle_actual),

        ### Relative np particle ratio (Yes these should be uncorrected.  Note uncorrected means including noise
        ### and not scaled to the entire fiber.
        
        # Equivalent ratios (WITHOUT NOISE) [THESE ARE PERHAPS MOST IMPORTANT IN DETERMINING CONTRIBUTIONS TO SPR]
        ('(%)singles_ratio_equiv_nonoise',r2(100.0* (float(self.single_counts) / self._np_total_equiv_nonoise))),
        ('(%)doubles_ratio_equiv_nonoise' ,r2(100.0* (float(self.double_particle_equiv) / self._np_total_equiv_nonoise))),               
        ('(%)mids_ratio_equiv_nonoise',r2(100.0* (float(self.flat_particle_equiv) / self._np_total_equiv_nonoise))),
        ('(%)bigs_ratio_equiv_nonoise',r2(100.0* (float(self.super_particle_equiv) / self._np_total_equiv_nonoise))),        
        
        # Equivalent ratios (WITH NOISE)
        ('(%)noise_ratio_equiv_wnoise' ,r2(100.0* (float(self.noise_particles) / self._np_total_equiv_withnoise))),
        ('(%)singles_ratio_equiv_wnoise',r2(100.0* (float(self.single_counts) / self._np_total_equiv_withnoise))),
        ('(%)doubles_ratio_equiv_wnoise' ,r2(100.0* (float(self.double_particle_equiv) / self._np_total_equiv_withnoise))),               
        ('(%)mids_ratio_equiv_wnoise',r2(100.0* (float(self.flat_particle_equiv) / self._np_total_equiv_withnoise))),
        ('(%)bigs_ratio_equiv_wnoise',r2(100.0* (float(self.super_particle_equiv) / self._np_total_equiv_withnoise))),
    
        # True ratios (nothing broken into equivalents), no noise
        ('(%)singles_ratio_actual_nonoise',r2(100.0* (float(self.single_counts) / self._np_total_actual_nonoise))),
        ('(%)doubles_ratio_actual_nonoise' ,r2(100.0* (float(self.double_particle_actual) / self._np_total_actual_nonoise))),               
        ('(%)mids_ratio_actual_nonoise',r2(100.0* (float(self.flat_particle_actual) / self._np_total_actual_nonoise))),
        ('(%)bigs_ratio_actual_nonoise',r2(100.0* (float(self.super_particle_actual) / self._np_total_actual_nonoise))),    
    
        #True ratios, with noise
        ('(%)noise_ratio_actual_wnoise' ,r2(100.0* (float(self.noise_particles) / self._np_total_actual_withnoise))),
        ('(%)singles_ratio_actual_wnoise',r2(100.0* (float(self.single_counts) / self._np_total_actual_withnoise))),
        ('(%)doubles_ratio_actual_wnoise' ,r2(100.0* (float(self.double_particle_actual) / self._np_total_actual_withnoise))),               
        ('(%)mids_ratio_actual_wnoise',r2(100.0* (float(self.flat_particle_actual) / self._np_total_actual_withnoise))),
        ('(%)bigs_ratio_actual_wnoise',r2(100.0* (float(self.super_particle_actual) / self._np_total_actual_withnoise)))
            
            )    
    

    @property
    def particle_analysis_parms_lite(self):
        ''' Particle analysis light summary parameters'''
        return(('nanoparticles', self.np_total_corrected),   
               ('IMJ particles (no noise)', self.true_particles_total_nonoise), 
               ('(%)singles_ratio_equiv_nonoise',r2(100.0* (float(self.single_counts) / float(self._np_total_equiv_nonoise)))),
               ('(%)doubles_ratio_equiv_nonoise' ,r2(100.0* (float(self.double_particle_equiv) / float(self._np_total_equiv_nonoise)))),               
               ('(%)mids_ratio_equiv_nonoise',r2(100.0* (float(self.flat_particle_equiv) / float(self._np_total_equiv_nonoise)))),
               ('(%)bigs_ratio_equiv_nonoise',r2(100.0* (float(self.super_particle_equiv) / float(self._np_total_equiv_nonoise))))
               )
               

    @property
    def np_size_parms(self):
        if self.xhismax and self.fit_sig:
            sizeparms=(('Min Size Criteria Met', self.mpx_crit_met),
                       ('Diam Est (%s)'%self.UNITS, r2(self.xhismax)), 
                       ('Sigma Est (%s)'%self.UNITS, r2(self.fit_sig)))
        else:
            sizeparms=(('Min Size Criteria Met', self.mpx_crit_met),
                       ('Diam Est (%s)'%self.UNITS, 'None'), 
                       ('Sigma Est (%s)'%self.UNITS, 'None'))   
        return sizeparms

    @property
    def protein_parms(self):      
        return( ('protein (cluster style/fill cracks)', self.bsa_parms_attstyle),
                ('Coverage style', self.bsa_cov_style),
  #              ('bsa range criteria', self.bsa_parms_numbers),
                ('bsa on singles',self.bsa_from_singles),
                ('bsa on doubles',self.bsa_from_doubles),
                ('bsa on mids',self.bsa_from_flats),
                ('bsa on bigs', self.bsa_from_supers),

                ### BSA percent weight distribution.  Should be quite close to np distribute, except
                ### considering that bsa singles are actually fit via a density distribution.
                ('%bsa singles',r2(100.0* (float(self.bsa_from_singles) / float(self._bsa_proportion)))),
                ('%bsa doubles',r2(100.0* (float(self.bsa_from_doubles) / float(self._bsa_proportion)))),
                ('%bsa mids',r2(100.0* (float(self.bsa_from_flats) / float(self._bsa_proportion)))),
                ('%bsa bigs',r2(100.0* (float(self.bsa_from_supers) / float(self._bsa_proportion)))),
                ('bsa total', self.bsa_total))   


    @property
    def protein_parms_lite(self):      
        return( ('protein (cluster style/fill cracks)', self.bsa_parms_attstyle),
        #        ('bsa range criteria', self.bsa_parms_numbers),
                ('Coverage style', self.bsa_cov_style),                
                ('%bsa singles',r2(100.0* (float(self.bsa_from_singles) / float(self._bsa_proportion)))),
                ('%bsa doubles',r2(100.0* (float(self.bsa_from_doubles) / float(self._bsa_proportion)))),
                ('%bsa mids',r2(100.0* (float(self.bsa_from_flats) / float(self._bsa_proportion)))),
                ('%bsa bigs',r2(100.0* (float(self.bsa_from_supers) / float(self._bsa_proportion)))),
                ('bsa total', self.bsa_total))   


    ### Instance methods ###
    def _set_image_parameters(self, image): 
        ''' Extracts a bunch of image-related parameters from the image file. Because I use
        this on the cropped file and infile, I left the image as a method parameter instead
        of calling self.image and setting all the values there.'''
        ### Set correct pixel scale if image is not 1024 x 768 ###
        pic = Image.open(image)

        ### Set picture scale ###
        unadjusted_scale=(100000 * self.mag_scale)/(self.mag)    
        resolution=pic.size
        scale=unadjusted_scale/ (pic.size[0] / 1024.0)   #Adjusts scale based on image resolution
        pixel_area=float(pic.size[0] * pic.size[1])
        picture_area=pixel_area* scale**2
        return (resolution, scale, picture_area)


    ### Scatter Matrix from Pandas ###
    def scatter_matrix(self, columns, alpha=0.2, figsize=(8,8), diagonal='kde'):
#        plt.clf()
#        plt.
        sm=scatter_matrix(self.count_results, alpha=alpha, figsize=figsize, diagonal=diagonal)


    ### Histogram-related methods ####        
    def greyscale_hist(self, **pltkwargs):  
        ''' Plot the greyscale histogram from imagej. '''

        outname=pltkwargs.pop('outname')
        intensity=[stat.pix_intensity for stat in self.grey_results]
        counts=[stat.count for stat in self.grey_results]

        plt.clf()
        plt.bar(intensity, counts, **pltkwargs)  #alpha, bins, etc..

        ### If user provides adjustment, just plot it
        if self.adjust:
            plt.axvline(x= self.adjust[0], color='blue', ls='-', lw=4)
            adj_text='Manual threshold (%d %d)' %  self.adjust 

        ### If automatic adjustment generated by imagej, it is in temporary file.  Open file, read values, plot, delete file.
        else:
            adj_file='%s/%s'%(self.outpath, 'adjustment.txt')
            f=open(adj_file, 'r')
            self.adjust=tuple([int(i) for i in f.readlines()[0].strip().split(',')]) #Read in adjustment from automatically generated imj file
            plt.axvline(x=self.adjust[0], color='r', ls='-', lw=4)        
            adj_text='Automatic threshold (%d , %d)' % self.adjust 
            f.close() ; os.remove(adj_file)

        ### Crop out the very white or very black pixels which are usually left over from image artifacts like the ziess logo or magnification.  These should
        ### not affect analysis post-thresholding/cropping, but this image is based on the original photo ###
        counts=counts[10:250]  ; intensity=intensity[10:250]  
        plt.xlim(intensity[0], intensity[-1]) 
        plt.ylim(min(counts), max(counts))  #MAKE THIS A VARIABLE LATER?

        plt.text(self.adjust[0]+10, max(counts)*.80, adj_text)    ## (LATER MAKE THIS WORK WITH AUTOMATIC ADJUSTMENTS- unindent     

        plt.title('Brightness Distribution'+' ('+self.shortname + ')')
        plt.ylabel('Counts')
        plt.xlabel(('Greyscale Intensity (Dark <-----> Bright)') )
        plt.savefig('%s/%s' %(self.outpath, outname) )

        return        

    def super_histogram(self, xattr, shadeattr=None, colorattr=None, lineattr=None,\
                        binnumber=None, mapx=None, special_outpath=None, savefig=True, **pltkwargs):
        ''' General histogram algorithm built to communicate with the data.  Savefig is an option
        because guassian fitting methods of this class also use this plot.'''

        outname=pltkwargs.pop('outname')  #Notice I add outname here
        plt.clf()
        legend_lines=[]   #Empty, fill up each time I want to add something to the legend.

        allattr=[xattr, shadeattr, colorattr, lineattr]
        allattr=[att for att in allattr if att] #Keep if not None
        subset=self.digiframe.subset(*allattr)
    # subset.sort_index(axis=0, by=xattr, ascending=True, inplace=True) #Sort by xcolumn (IMPORTANT)

        ### set limits on data range ###
        lrange=pltkwargs.pop('lengthrange') #Will be NONE if user doesn't pass anything in
        if lrange:
            x_min, x_max=lrange
        else:
            x_min, x_max=subset[xattr].min(), subset[xattr].max() #Although sorted could just do [0] , [-1] but 
                                                                    #this is safer if code changes ever

        if not binnumber:        #Useful for making histograms not based on internal size parameters.
            binnumber=self.digiframe.bin_number  
        binwidth=get_binwidth(subset[xattr], binnumber)  


        ### ADD SOMETHING HERE TO COMPUTE BINWIDTH GIVEN BINNUMBER            

        ### Plot the x-axis histogram as the main histogram ###
        counts, bin_edges, patches=plt.hist(subset[xattr], bins=binnumber, **pltkwargs)  
        bincenters=get_bin_points(bin_edges, position='c')
        bininds=np.digitize(subset[xattr], bin_edges)
        xhismax, yhismax=hist_max(counts, bincenters, idx_start=0, idx_stop=None)[1:3]   #For use later     

        xname=xattr  #Used for outputting onto plot, don't want to overwrite the attribute   

        #### Correct for logarithms name:function, out representation ###   
        #valid_maps={'10':(np.log10, 'LOG10'), '2':(np.log2, 'LOG2'), '1p':(np.log1p,'LOG1p'), 
                    #'e':(np.log,'LOGe')}

        #if mapx:     #name and cause errors later if I refer back to it
            #try:
                #mapfunction, mapname=valid_maps[str(mapx)]
            #except KeyError:
                #raise KeyError('Invalid mapping base passed into histogram function: must be LOG 10, 2, 1p or e')
            #else:
                #xvals=mapfunction(xvals)
                #xname='%s %s'%(mapname, xname)
                #x_min, x_max=mapfunction(x_min), mapfunction(x_max) 

        ### Fit plot axis' to current data ranges.  This code finds the bin edges where xmin and xmax occur.
        ### It takes the index of these edges and puts it into the histogram count data, and gets the ymax value
        plt.xlim(x_min, x_max)
        y_min=0
        ### Find bins of max and min on dataset ###
        binmax_ind, binmin_ind=self._find_nearest(bin_edges, x_max)[0], self._find_nearest(bin_edges, x_min)[0]
        y_max=max(counts[binmin_ind: binmax_ind])  #Takes it from the sampled dataset
        y_extra_space=1.10 #Add 10% extra space at top of plot
        plt.ylim(y_min, y_max*y_extra_space)


        plt.title('%dX %s Distribution (%s %s < %s < %s  %s)' %(self.mag, xattr, round(x_min,0), \
                                                                self.UNITS, xname, round(x_max,0), self.UNITS))
        
        plt.ylabel('Counts')
        plt.xlabel(('%s (%s)') %(xname, self.UNITS) )

        ### Custom major xticks ###
        plt.minorticks_on() #Minor ticks automatically taken care of          
        tick_spacing=(x_max - x_min ) * 0.1 #5 major ticks per plot
        ticks=list( [round(i,1) for i in np.arange(x_min, x_max, tick_spacing)] )     #from rounding
        ### Glitch:  Want to do plt.xticks(ticks, labels) but then it requires equally spaced 
        plt.xticks(ticks) #Set the correct tick spacing         

        if colorattr:
            raise NotImplementedError('Need to build color attribute stuff')

        #### Color in patches based on a parameter (circularity)###        
        if shadeattr:
            default_fill=0.1 #If no weight from shaded attribute
            if shadeattr=='circ':  #PUT SOMETHING ABOUT THIS IN LEGEND
                weight_max=1.0
            else:
                weight_max=None 
            sweights=digitize_by(subset, bininds, avg_fcn='weighted', weight_max=weight_max)[shadeattr]
            for i, patch in enumerate(patches):
                try:
                    patch.set_alpha(default_fill + (1.0-default_fill)*sweights[i]) #Should be 0.0 if index has no population
                except KeyError:
                    pass


        ##### Plot bound lines based on parameter ###
        if lineattr:
            ### Set x-line min/max boundaries ###
            hbound_low, hbound_high = 0, y_max
            hcolor, hstyle, pointcolor='r', '-', 'b'

            plt.axhline(y=hbound_low, linestyle=hstyle, color=hcolor)    
            plt.axhline(y=hbound_high, linestyle=hstyle, color=hcolor)    

            ### Normalize cbin data to fit between y_max/2.0 and y_max ###
            ys=[] #y points of scatter [(bin_mid1, 3.4), (bin_mid2, 2.3)]


            if lineattr=='circ':  #PUT SOMETHING ABOUT THIS IN LEGEND
                weight_max=1.0     
            else:
                weight_max=None  

            lweights=digitize_by(subset, bininds, avg_fcn='weighted', weight_max=weight_max)[lineattr]

            for i, bmid in enumerate(bincenters):
                try:
                    ys.append(hbound_low + (hbound_high-hbound_low) *lweights[i])  #WILL ERROR IF YAUTO IS NOT ON!
                except KeyError:
                    ys.append(hbound_low ) #LaTER MAKE THIS YMAX/2
            plt.scatter(bincenters, ys, color=pointcolor)




        plt.legend( legend_lines, fancybox=True)  #NEED TRAILING COMMA (xname,) FOR CORRECT FORMATTING        

        outname=outname+'_lineatt-%s'%(lineattr)

        if savefig:
            if special_outpath:
                plt.savefig('%s/%s' %(special_outpath, outname) )              
            else:
                plt.savefig('%s/%s' %(self.outpath, outname) )

    ### ImageJ-related Methods

    def make_imjmacro(self, out_original=True, out_circles=True, out_thresh=True, out_summary_full=True):

        if not self.particle_parms:
            raise AttributeError('Cannot make imjmacro without imagej parameters (r, c, despeckle etc...)')

        imjmacro=[]  #Commands are input as list of strings then joined at the end

        imjmacro.append('open("%s");' %self.image)

        ### Crop before any thresholding is best bet.  Then all threshold-related files aren't based on non-cropped image##   
        if self.crop:
            imjmacro.append('//setTool("rectangle");')        
            imjmacro.append('makeRectangle(%d, %d, %d, %d);'%(self.crop))
            imjmacro.append('run("Crop");')
            self.cropped_file="%s/%s_cropped.tif" %(self.outpath, self.shortname_noext)
            imjmacro.append('saveAs("Tiff", "%s");' % self.cropped_file )        



        ### Necessary to generate and save histogram data through imagej itself ###
        self.greyscale_file="%s/%s_greyscale.txt"%(self.outpath, self.shortname_noext)    
        imjmacro.append('getHistogram(values, counts, 256);')
        imjmacro.append('d=File.open("%s");'% self.greyscale_file)
        imjmacro.append('getThreshold(threshold, max);')
        imjmacro.append('for (k=0; k<values.length; k++) { print(d, k+" "+counts[k]);}')
        imjmacro.append('File.close(d);') 


        imjmacro.append('run("Set Scale...", "distance=1 known=%s pixel=1 unit=%s");'%(self.min_pixel_length, self.UNITS))
        #imjmacro.append('setAutoThreshold("Default dark");')
        imjmacro.append('//run("Threshold...");')  #This brings up threshold toolbar/menu
        ### If adjustment manually set, do that.  Otherwise, autoadjust ###
        if self.adjust:
            imjmacro.append('setThreshold(%d, %d);'%(self.adjust))   #manual threshold
        else:
            imjmacro.append('setAutoThreshold("Default dark");')

            ### Sloppy patched way to get imagej adjustment threshold
            imjmacro.append('d=File.open("%s/%s");'%(self.outpath, 'adjustment.txt'))
            imjmacro.append('getThreshold(threshold, max);')
            imjmacro.append('print(d, threshold + "," + max);') #
            imjmacro.append('File.close(d);')            

        if self.particle_parms['despeckle']:
            imjmacro.append('run("Despeckle");')   

        imjmacro.append('''run("Set Measurements...", "area mean standard modal min centroid center perimeter bounding fit shape feret's integrated median skewness kurtosis area_fraction stack limit redirect=None decimal=3");''')

        imjmacro.append('run("Analyze Particles...", "size=%s-%s circularity=%s-%s show=Ellipses display clear exclude summarize");'  #exclude is exclude on edges
                        %(self.particle_parms['rsmall'], self.particle_parms['rlarge'], self.particle_parms['csmall'], self.particle_parms['clarge']))

        if out_summary_full:
            self.results_file="%s/%s_stats_full.txt" %(self.outpath, self.shortname_noext)
            imjmacro.append('saveAs("Results", "%s");' %self.results_file )


        ### CHANGE THIS TO ALLOW FOR SEVERAL OUTPUTS! ###
        if out_circles:
            self.circles_file="%s/%s_circles.tif" %(self.outpath, self.shortname_noext)
            imjmacro.append('saveAs("Tiff", "%s");' %self.circles_file )    
            imjmacro.append('close();')  #Closes the circles window


        ###### Take a count of just the black and just the white pixels ######
        imjmacro.append('//run("Threshold...");')
        imjmacro.append('run("Convert to Mask");')                    
        self.bw_file="%s/%s_blackwhite.txt"%(self.outpath, self.shortname_noext)        
        imjmacro.append('getHistogram(values, counts, 256);')
        imjmacro.append('d=File.open("%s");'%self.bw_file)
        imjmacro.append('getThreshold(threshold, max);')
        imjmacro.append('for (k=0; k<values.length; k++) { print(d, k+" "+counts[k]);}')
        imjmacro.append('File.close(d);')

        ### Save black/white picture file ###
        if out_thresh:               
            self.thresh_file="%s/%s_adjusted.tif"%(self.outpath, self.shortname_noext)
            imjmacro.append('saveAs("Tiff", "%s");' %self.thresh_file  )           


        #if out_summary_full:
            #self.results_file="%s/%s_stats_full.txt" %(self.outpath,self.shortname)
            #imjmacro.append('saveAs("Results", "%s");' %self.results_file )


        #### CHANGE THIS TO ALLOW FOR SEVERAL OUTPUTS! ###
        #if out_circles:
            #self.circles_file="%s/%s_circles.tif" %(self.outpath,self.shortname)
            #imjmacro.append('saveAs("Tiff", "%s");' %self.circles_file )     

        imjmacro.append('close();')    

        fullmacro='\n'.join(imjmacro)  ## Create the full macro

        ### Output the macro
        self.macrofile='%s/%s.ijm'%(self.outpath,self.shortname)
        o=open(self.macrofile, 'w')
        o.write(fullmacro)
        o.close()

        ### Output a copy of the original image ###    
        if out_original:
            shutil.copy(self.image, self.outpath)  

        return 

    def run_macro(self):  
        # To run non-interactively in batch mode, ImageJ has to read a macro from disk.
        # The third parameter is the image to be processed.

        command = "%s -batch %s" % (path_to_imagej, self.macrofile) 
        logger.info("Running IMJMACRO: %s" % command)

        # Output to /dev/null (which auto-deletes)
        with open(os.devnull, 'w') as dnull:
            p = subprocess.call(command, shell=True, stdout=dnull)# stderr=subprocess.PIPE)
            
        logger.info('IMJ Counting complete!')

    def initialize_count_parameters(self, infile=None):
        ''' Initialize a class for storing imagej statistical data that is necessary for advanced
        analysis.  Optional infile can be passed; otherwise, this uses self.results_file'''
        if not infile:
            infile=self.results_file
        df = to_dataframe(from_file(results_manager, infile, parsecomments=True))
        ### Add two psuedo columns length and psuedod (diamter converstion assuming a circle) ###
        lengths = np.sqrt(df.area)
        psuedo_d = 1.13*np.sqrt(df.area)
	new = DataFrame({'length':lengths, 'psuedo_d':psuedo_d})

	df = df.join(new)
        self.digiframe = MultiHistMaster(dataframe=df) #Populated when count results is called       
        self.digiframe._set_binnumber_from_data_binwidth('length', self.min_pixel_length)         

    def _quick_slice(self, wrange, series):
        ''' Convienence method to slice ranges of data for coverage analysis.
            Series can be a field string, and if so, this will default to slicing self.count_results to 
            get the series out.'''
        if len(wrange) != 2:
            raise AttributeError('Range attribute in protein_coverage_analysis must be len 2 (start, stop)')               

        if isinstance(series, basestring):
            series=self.count_results[series]
        
        return range_slice(series, start=wrange[0], stop=wrange[1], style='value') 
    
    def _quick_frame(self, idx_or_series, attr=None):
        ''' Given a series with integer index (or array of integer labels)
            and returns the full dataframe of just these values.  If attr specified, this
            only returns the series of that attribute instead of full dataframe.
            
            Useful for, say, you get a series of diamteres from quick_slice and want the corresponding
            circularities of these.  You can pass the output of quick_slice right in here and it will 
            return a dataframe of all rows corresponding to the indicies of hte original series,
            or just the attr column.
            
            Example:  Have series of diameters, want the actual areas or circularities corresponding'''
        
        if isinstance(idx_or_series, Series):
            idx=idx_or_series.index
        else:
            idx=idx_or_series
        
        outframe=self.count_results.ix[idx]
        if attr:
            return outframe[attr]
        else:
            return outframe

    def _protein_count(self, series, bsa_countstyle, wrange=None):
        ''' Convienence method to take a range of diameters, get the interpolated particle per area density,
        and then return an array of predicted number of proteins.
        
        kwds:
          series: series data of diameter values.
          basecountstyle: see bsa count() method
          wrange: convienence method to slice data further.'''
        ### Diameter of single particles
        if wrange:
            diams=self._quick_slice(wrange, series)
        else:
            diams=series
        ### bsa per area density for each particle
        ### This is 4pi **2 for individual particles.  Only supers need to be treated as halfspheres
        bsa_per_surf_area=bsa_count(diams, style=self.bsa_countstyle)
        surface_areas=diams.apply(lambda x: (pi * x**2 )) #4 pi r**2 = pi d**2

        ### Molecules/area * area = # particles. 
        return (bsa_per_surf_area*surface_areas).apply(lambda x: roundint(x))   

    def coverage_analysis_basic(self, single_range, single_mean, protein='BSA', attstyle='psuedo_d', 
                                flat_range=None, super_adj_style=None, super_fill_in_cracks=False):
        '''Method to estimate protein coverage and NP counts.  For now, only BSA is supported, and estimates of np coverage
               are based on NIST paper.  A bsa binding density line is fit between 10, 30, 60nm nps.  Program works 
               as follows:
                  NP's in the single range (start, stop) are assigned protein coverage based on the assumption
                  of sphericity.  

                  kwds:
                    -attstyle allows user to change between representations of data.
                    -If remove_low_coverage, particles under the single_start threshold are actually subtracted from
                     imagej's bwcoverage estimation.  Not sure how this will affect low mag images.
                    -flat_range is range where aggregates are taken as larger than single particle, but not piling up.
                     Therefore, their area is tallied by assuming they are multiples of the single_mean.
                     -super_range is automatically determined from the upper limit of flat range, and ends at upper limit
                     of dataset.
                    - Remove low coverage:Any particles smaller than single_start are actually removed from the estimate of the initial estimate
                  of coverage. 

                  Due to nice behavior of pandas dataframe/series, if no particle in size ranges, nothing errors and returns 0.
                  '''       
        if protein != 'BSA':
            raise NotImplementedError('Protein must be BSA in protein_coverage_analysis()')
        if attstyle != 'psuedo_d':
            raise NotImplementedError('Attribute must be psuedo_d in coverage_analysis_advanced()')


        ### Store coverage on a single bsa particle for use with flat and super aggregation functions
        bsa_per_surf_area=bsa_count([single_mean], style=self.bsa_countstyle)[0]
        single_mean_area=(pi * single_mean**2)  #4 pi r**2 = pi d**2 (think about )
        mean_particle_bsanumber=(bsa_per_surf_area*single_mean_area) 

        ### COMPUTE BSA ON SINGLES
        singles=self._protein_count(self.count_results[attstyle], self.bsa_countstyle, wrange=single_range)
        self.bsa_from_singles, self.single_counts=singles.sum(), len(singles)

        ### Particles that are NOISE d=0 up to d=singles_min ###
        noise_particles=self._quick_slice((0.0, single_range[0]), self.count_results[attstyle])
        self.noisy_area=noise_particles.apply(lambda x: (pi * x**2 / 4.0)).sum()
        self.noise_particles=len(noise_particles)

        ### Store these for attribue  for output/summary record ###
    #    self.bsa_parms_numbers='0.0-%s, %s-%s, %s-%s'%(single_range[0], single_range[0],\
                             #                          round(single_range[1],2), round(flat_range[0],2), flat_range[1]) 
        self.bsa_parms_attstyle='%s, %s'%(super_adj_style, super_fill_in_cracks)

        ### May want to let these depend on area and relax condition of psuedo-d
        if flat_range:
            ### Extract mid-sized aggregates, get particle counts assuming aggregates of mean size 
            flats=self._quick_slice(flat_range, self.count_results[attstyle])
            self.flat_particle_actual=len(flats)

            ### WHY ROUND
            flats_count=flats.apply(lambda x: x/single_mean).sum()  
            ### Now I have the total number of particles that are assumed to be of size single_mean
            bsaflat=flats_count*mean_particle_bsanumber

            ### Store counts of bsa and predicted NP equivalent counts
            self.bsa_from_flats, self.flat_particle_equiv=roundint(bsaflat), roundint(flats_count) #Yes, roundint( needed

            ### Large aggregates, bigger than flat_range start to max of data +1 to include                        
            super_range=(flat_range[1], max(self.count_results[attstyle]))
            supers=self._quick_slice(super_range, self.count_results[attstyle])
            self.super_particle_actual=len(supers)
            ### Reduce big particles in many mean-sized particles
            if super_adj_style == None:
                supers_count=supers.apply(lambda x: x/single_mean).sum()
                bsasupers=supers_count*mean_particle_bsanumber                  

            elif super_adj_style == 'hemisphere':
                ### Number of np's is the ratio of volume of halfsphere to full average NP
                supers_count=supers.apply(lambda x: 0.5 * (x**3 / single_mean**3)).sum() 
                
                ### If fill in cracks, use all the surface area of the total number of NP's in the halfsphere 
                ### as bsa binding sites
                if super_fill_in_cracks:
                    bsasupers=supers_count*mean_particle_bsanumber  
  
                ### Take SA of half sphere and divide by equivalent number of np's it would take to make that SA
                ### then apply bsa binding to that equivalent surface area
                else:
                    bsasupers=mean_particle_bsanumber * supers.apply(lambda x: (0.5 * x**2 / single_mean**2)).sum()

            self.bsa_from_supers, self.super_particle_equiv=roundint(bsasupers), roundint(supers_count)

            self.bsa_cov_style='Basic'

        else: 
            raise NotImplementedError("Non-flat range input is not handled yet in curve analysis basic")    


    def coverage_analysis_advanced(self, flat_high, single_low=None, single_high=None, curve_cutoff=None, protein='BSA', attstyle='psuedo_d', 
                                    super_adj_style=None, super_fill_in_cracks=False):
        '''Read curve_analysis_basic before trying to understand this method.  This method works
        in a similar manner, but required too much adjustment to merge into a single method.
        
        Uses internally stored fit with a single maximum (usually a guassian).  From this, the mean particle
            diameters is taken to be the maximum of the function.  It is then superimposed onto the histogram created
            when self.hist_bestfit() is run.  Depending on how this curve intersects the histogram, it will 
            decide how many particles to the right of the mean are large singles, and how many are small doubles.

        THIS METHOD REQUIRES THAT HIST_BESTFIT() HISTOGRAM HAVE A FIT TO IT


           kwds:
            flat_high
             - Promoted this to a mandatory input, since flat low is taken automatically from the best fit bin.            
           
            single_low
             - Lowest diameter to count that is not considered noise.  If not passed, program uses
               self.fit_xmin (eg point where fit goes to self.about_zero

            curve_cutoff
             - Y value below which curve becomes 0.  Used to determine when to stop doubles/singles region and
               begin flat aggregates region.  Default is self.about_zero
                                   '''

        if protein != 'BSA':
            raise NotImplementedError('Protein must be BSA in protein_coverage_analysis()')
        if attstyle != 'psuedo_d':
            raise NotImplementedError('Attribute must be psuedo_d in coverage_analysis_basic()')
        
        dataset=self.count_results[attstyle]

        try:
            counts, bins, patches = self.histogram
        except Exception:
            raise AttributeError('Before calling coverage_analysis_advanced, hist and best fit must be run \
                                  otherwise, internal histogram is never stored.')
        
        ### Set keywords if not defaulted
        if not curve_cutoff:
            logger.debug('Setting curve_cutoff coverage_analysis_advanced to self.bout_zero')
            curve_cutoff = self.about_zero

        ### Take single particle mean from optimized guassian.  If no autogaussian, takes it from histogram max.
        if self.fit_mean:
            single_mean=self.fit_mean
        else:
            single_mean=self.xhismax
                
        ### Set bounds on singles low/high from manual parameters, autogaussian or histogram
        if not single_low:
            if self.fit_min_max[0]:
                single_low=self.fit_min_max[0] #Uses fitmax as entry condition to save redundancy below
            else:
                logger.warning('%s: Coverage analysis lower particle size cutoff could not be'
                               ' derived from guassian fit!  Instead, applying it as half the diameter'
                               ' of the max bin on the diameter histogram.' % self.image)
                single_low=0.5*self.xhismax
                
        if not single_high:
            if self.fit_min_max[1]:
                single_high=self.fit_min_max[1]
            else:
                logger.warning('%s: Coverage analysis upper particle size cutoff could not be'
                 ' derived from FIT!  Instead, applying it as 1.5 times the diameter'
                 ' of the max bin on the diameter histogram.' % self.image)
                single_high=1.5*self.xhismax       

        ### Ensure floats        
        single_high, single_low = float(single_high), float(single_low)
        
        ### Set bounds on doubles range
        if self.fit_mean:
            #1 standard deviation up to 2*mean)
            doubles_low=  self.fit_sig+self.fit_mean
            doubles_high= 2.0*self.fit_mean
        else:
            #index of max bin + 4 (eg 4 bins to right of max)
            bins_past_mean=4
            doubles_low=  bins[self.idxhismax+bins_past_mean]
            doubles_high= 2.0*self.xhismax
            
        flat_low=doubles_high+0.001 #avoid double counting
        flat_range=(flat_low, flat_high)
            
        if doubles_low > single_high:
            raise Exception('%s: Error in coverage analysis, doubles low is greater than singles high.  This can happen'
                            ' when histogram has a large peak in noise region.' % self.image)       
            
        bsa_per_surf_area=bsa_count([single_mean], style=self.bsa_countstyle)[0]
        single_mean_surfarea=(pi * single_mean**2)
        mean_particle_bsanumber=(bsa_per_surf_area*single_mean_surfarea) 

        #### Particles that are NOISE d=0 up to d=singles_min ###
        noise_particles=self._quick_slice((0.0, single_low), dataset)
        self.singles_low=single_low #Used for slicing out noise in noiseless particle coverage
        self.noise_particles=len(noise_particles)

        #### From singleslow to doubles start range, compute estimations of np's from the data itself
        #### and not from the binned data.
        left_range=(single_low, doubles_low)  
        self.single_particles=self._quick_slice(left_range, dataset)

        ### From the bin closests to doubles low and use it to start sampling data.
        bin_start, count_start=self._find_nearest(self.bincenters, doubles_low)
        bin_end, count_end=self._find_nearest(self.bincenters, single_high)
        if count_end > single_high: 
            bin_end=bin_end-1  #Always want to count bins up to the left of singles_high
        
        ### Partition data between singlehigh and doubles low by splitting histogram bins and resampling
        working_centers=self.bincenters[bin_start:bin_end+1]
        working_lefts=self.binlefts[bin_start:bin_end+1]
        working_rights=self.binrights[bin_start:bin_end+1]

        # If fit, slice right end to get better resolution on doubles/singles
        if self.fit_mean:
            hist_dubs=Series(); hist_singles=Series()
        
            ### Use fit to split data between singles/doubles and append to a running series
            fitpoints=self.best_fit(self.bincenters[bin_start:bin_end+1])
            for i, c in enumerate(working_centers):
                l, r, height = working_lefts[i], working_rights[i], fitpoints[i]
                sing, dub=bin_above_below(dataset, l, r, height, shuffle=False)
                if len(dub) != 0:
                    hist_dubs=hist_dubs.append(dub)
                if len(sing) != 0:
                    hist_singles=hist_singles.append(sing)

            self.double_particles=hist_dubs.append(self._quick_slice((r, doubles_high), dataset))    
            self.single_particles=self.single_particles.append(hist_singles)        
        
        else:
            logger.warning('%s: Double particles may be overestimated due to no guassian fit.' % self.image)
            self.double_particles=self._quick_slice((doubles_low, doubles_high), dataset)        
        

        self.bsa_from_singles=self._protein_count(self.single_particles, self.bsa_countstyle).sum() #SERIES RETURNED IF NEEDED
               
        ### Get bsa on halfed particles, then double count.  
        npdoubles=self.double_particles/2.0
        self.bsa_from_doubles=2.0 * self._protein_count(npdoubles, self.bsa_countstyle).sum()
        self.double_particle_equiv=2.0*len(self.double_particles)      
                       
        ### Extract mid-sized aggregates. 
        flats=self._quick_slice( (flat_range), dataset)
        self.flat_particle_actual=len(flats)
        flats_count=flats.apply(lambda x: x/single_mean).sum()
            
        ### Now I have the total number of particles that are assumed to be of size single_mean
        bsaflat=flats_count*mean_particle_bsanumber

        ### Store counts of bsa and predicted NP equivalent counts
        self.bsa_from_flats, self.flat_particle_equiv=roundint(bsaflat), roundint(flats_count)

        ### MAKE THIS A PRIVATE METHOD!!
        ### Large aggregates, bigger than flat_range start to max of data +1 to include                        
        super_range=(flat_range[1], max(dataset))
        supers=self._quick_slice(super_range, dataset)
        self.super_particle_actual=len(supers)
        
        # Compute area-breakdown of various components (FOR FILL FRACTION STUFF)
        self.noisy_area = self._quick_frame(noise_particles, 'area').sum()
        self.singles_area = self._quick_frame(self.single_particles, 'area').sum()
        self.doubles_area = self._quick_frame(self.double_particles, 'area').sum()
        self.flats_area = self._quick_frame(flats, 'area').sum()
        self.supers_area = self._quick_frame(supers, 'area').sum()
        
        # Reduce big particles into multiples of mean-sized particles        
        if super_adj_style == None:
            supers_count = supers.apply(lambda x: x/single_mean).sum()
            bsasupers = supers_count*mean_particle_bsanumber  

        elif super_adj_style == 'hemisphere':
            # Number of np's is the ratio of volume of halfsphere to full average NP
            supers_count = supers.apply(lambda x: 0.5 * (x**3 / single_mean**3)).sum()             
            
            ### If fill in cracks, use all the surface area of the total number of NP's in the halfsphere 
            ### as bsa binding sites
            if super_fill_in_cracks:
                bsasupers=supers_count*mean_particle_bsanumber  

            ### Take SA of half sphere and divide by equivalent number of np's it would take to make that SA
            ### then apply bsa binding to that equivalent surface area
            else:
                bsasupers=mean_particle_bsanumber * supers.apply(lambda x: (0.5 * x**2 / single_mean**2)).sum()

        self.bsa_from_supers, self.super_particle_equiv=roundint(bsasupers), roundint(supers_count)


        ### Didn't put double range in because it's inferred from 2.0*single_range
#        self.bsa_parms_numbers='0.0-%s, %s-%s, %s-%s'%(single_low, single_low,\
 #                                                      round(single_mean,2), round(flat_range[0],2), flat_range[1]) 
        self.bsa_parms_attstyle='%s, %s'%(super_adj_style, super_fill_in_cracks)       

        self.bsa_cov_style='Advanced'
        


    def hist_and_bestfit(self, attstyle='psuedo_d', special_outpath=None, special_outname=None,\
                         savefig=True, smart_bin_range=None, binnumber=None, l_left=0.35, show_fit_points=True,
                         showleft=True, showright=True, showdub=True):
        ''' Stores a histogram of lengths and adds optimized guassian.  Figured it be best to sore
        an internal representation as mean data is important for outfile.  Redundancy with super_histogram().
        
        RETURNS: FUll path to plot that was generated

           Uses an emprical parameter mpx critical to decide when the optimization would work.  mpx of 3.1nm
           is about 30000k high res, which is the criteria cutoff.

           If saveplot, this will generate a plot using _plot_hist_best_fit.  If not, it will still set 
           attributes which may be necessary for output.

           This method will work for either canonical length attribute or "psuedo_d" (aka force-fitted diameters).
           For spheres, related by a factor of 1.13.

           Alot of things can cause this to glitch.  For example, if there aren't many particle in an image, then
           the histogram is unlikely to find a maximum corectly.  Added a smart_bin_range keyword to let users sort of
           set the limit over which the maximum could or could not be found.  This should have excessive leighweigh,
           just because looking for maxes along ranges isn't always great.

           L_Left determines percentage left from center of the histogram to include in an automatic
           guassian fitting routine for size estimations of the particles.

           Yields 6 new attributes:
           self.xhismax, self.yhismax (bin center coordinates of max x and y)
           self.fit_mean, self.fit_sig (fit mean and standard deviation to histogram)
           self.fit_amp (not sure... haven't used them.  More useful when plotting best fit line).
           
           showleft/right/dub: plot a verticle line at point that indicates singles boundaries and
                               doubles upper limit.'''



        ### User can either do this for length, or 
        if attstyle=='length':
            wrange=(8.8, 88.0) #d=10-100nm                
            xlabel='Pixel Length %s'%self.UNITS
        elif attstyle=='psuedo_d':
            wrange=(10.0, 100.0)  #Diameter upconversion constant (d=10,100)
            xlabel='Approx. Diameter %s'%self.UNITS
            
        elif attstyle=='area':
            wrange=(0.0, 7000.0)
            xlabel='Area nm^2'
        else:
            raise AttributeError('Attribute style %s not supported in hist_and_bestfit() method'%attstyle)

        ### Set internal bin number, or use it.  Important to keep it stored for protein analysis methods.
        if binnumber:
            self._binnumber=binnumber
        else:
            binnumber=self._binnumber

        working=range_slice(self.count_results[attstyle], start=wrange[0], stop=wrange[1], style='value')

        ### Even if I don't save plot, just easier to do this 
        plt.clf()
        counts, bin_edges, patches=plt.hist(np.array(working), bins=binnumber, color='green', alpha=0.4) 

        bincenters=get_bin_points(bin_edges, position='c')
        
        ### Store copy of internal histogram, as aggregation functions may rely on it!
        self.histogram=counts, bin_edges, patches

        ### Relax this if fitting a manual guassian, or maybe let this method try to coarse data!
        ### User can sort of force min, max or both and this will make sure regions are cut out of histogram  
        if smart_bin_range:
            if len(smart_bin_range) != 2:
                raise AttributeError('Smart bin range must be length two oject between \
                working ranges %d - %d'%lrange[0], lrange[1])
            idx_start=self._find_nearest(bincenters, smart_bin_range[0])[0]
            idx_stop=self._find_nearest(bincenters, smart_bin_range[1])[0]

        else:       
            idx_start=1
            idx_stop=None           

        bininds=np.digitize(working, bin_edges)
        idx_center, center_x=hist_max(counts, bincenters, idx_start=idx_start, idx_stop=idx_stop)[0:2]
        self.idxhismax, self.xhismax, self.yhismax=hist_max(counts, bincenters, idx_start=idx_start, idx_stop=idx_stop)   #For use later                

        ### Define distance left percentage to probe histogram fit.  
        idx_left=self._find_nearest(bincenters, (center_x*(1.0-l_left)))[0]

        ### Fit a line of best fit to histogram using only left-data range selected ###
        if not self.mpx_crit_met:  
            logger.critical('%s: Image minimal pixel criteria not met!  Histogram fitting will not be attempted.'
                            'Particle counting from histogram is likely to be highly inaccurate if the maxbin'
                            ' is withing the noise region.' % self.image)
            
        else:

            try:
                
                logger.info("Attempting to fit histogram with curve.")
                symm_counts, symm_centers=psuedo_symmetric(counts, bincenters, idx_start=idx_left)          
        
                ### Fit a shorten, optimized gaussian to the data ###
                short_gauss, self.fit_amp, self.fit_mean, self.fit_sig=optimize_gaussian(symm_counts, symm_centers)     
                self.fit_attribute = attstyle
                
            except Exception as Exc:
                logger.critical('%s: Fitting of the histogram failed.  All coverage data will be based on histogram counts!' % self.image) 
                

        if savefig:

            plt.xlabel(xlabel)
            plt.ylabel('Counts')                

            ### Relax this if fitting a manual guassian, or maybe let this method try to coarse data!
            if self.best_fit:  ### Is this the best condition?

                #### Trace and plot line automatic gaussian/line of best fit
                #if self.fit_min_max:
                fitmin, fitmax = self.fit_min_max[0], self.fit_min_max[1]
                if fitmin and fitmax:                    
                    xfunc=np.arange(self.fit_min_max[0], self.fit_min_max[1], self.dx)
                    plt.plot(xfunc, self.best_fit(xfunc), color='blue')
         
                else:       
                    plt.plot(bincenters, self.best_fit(bincenters), color='black', ls='--')
                
                ###Make top of plot 5% higher than max bin.  Necessary to have this for vlines 
                yviewmax=1.05*self.best_fit(bincenters).max()
                plt.ylim(0.0, yviewmax)
                
                
                ### Highlight the patches that were used int he fit.  Verified correct slicing.
                if show_fit_points:
                    for patch in patches[idx_left:idx_center+1]:
                        patch.set_color('pink') #Lots of ways to customize this, like doing stripes/border etc.

                ### Draw flank lines where gaussian considered 0.  Useful for particle counting later.
                if self.fit_min_max:
                    xleft, xright = self.fit_min_max

                    if showleft:
                        plt.vlines(xleft, 0.0, yviewmax, color='r', linestyles='dashed')                        
                        
                    if showright:
                        plt.vlines(xright, 0.0, yviewmax, color='r', linestyles='dashed')                        

                if showdub:
                    if self.doubles_range:
                        plt.vlines(self.doubles_range[1], 0.0, yviewmax, color='g', linestyles='dashed')                        
                        


                fmat = lambda x:str(round(x,1))  

                plt.title('Guassian Fit Range   %s - %s (%s)'%(fmat(center_x*(1.0-l_left)), fmat(center_x), self.UNITS))
                plt.minorticks_on()


                ### Add text about guassian moments                     
                xpos=.7*float(plt.xlim()[1]) ; ypos=.7*float(plt.ylim()[1])
                fmat=lambda x: str( round(x,1)) + ' ' + self.UNITS
                plt_txt='$ \mu=$ %s \n $\sigma=$ %s\n x=%s\n y=%s' \
                    %(fmat(self.fit_mean), fmat(self.fit_sig),  fmat(self.xhismax ),  str(self.yhismax)+' counts' )  
                plt.text(xpos, ypos, plt_txt, fontsize=15)  

            else:
                plt.title('Guassian Fit Range   {Fit not found}')

            if special_outname:
                outname=special_outname
            else:                
                outname='%s_fithist'%attstyle
                
            if special_outpath:
                plotpath = op.join(special_outpath, outname)
            else:
                plotpath = op.join(self.outpath, outname)
                
            plt.savefig(plotpath)
            return plotpath
                
            ### This fits a guassian based on the data using an emperical mean, but is
            ### incomplete and should not be used if optimization is working fine.
            #symm_gauss=fit_normal(symm_counts, symm_centers)
            #xline=plt.plot(symm_centers, symm_gauss, 'b--')   
            #legend_lines.append('Manual gaussian')            


    def scale_data_from_hist(self, newmean, try_curve=True, attstyle='psuedo_d', **histbestfit_kwargs):
        ''' Scales the count_results data by a percentage computed by the 
            % diff between newmean and the predicted mean of the current
            histogram or best fit curve.
            
            Parameters:
            -----------
            
               newmean: Mean to which user wants to force into binned data.
               try_curve: If true, this will scale based on the mean of the
                          best fit curve to this histogram and not to the max
                          bin.
                histbestfit_kwargs: Kwargs passed to hist_and_bestfit function.
                                    Useful for changing if refit histogram is
                                    replotted or not.
                          
            Explanation:
            ------------
                Images of particles taken from SEM for example often have
                thresholding errors that cause under or overestimation of 
                particle sizes.  As such, the binned data tends to incorrectly
                predict the particle mean size.  This method rescales the 
                raw data by a scale factor computed as the percent difference
                of the histogram (or best fit) mean from that of the desired 
                mean.  After rescaling, it regenerates the histogram and
                curve fit (if one already exists).
                          
            '''

        if attstyle != 'psuedo_d':
            raise NotImplementedError('Attribute must be psuedo_d in coverage_analysis_basic()')
        
        if self.uncorrected_dmean:
            raise AttributeError('Design prohibits correcting for dmean more than once per image.')

        ### If newmean is None, return.  Else, convert to float
        if not newmean:
            return
        newmean = float(newmean)               
        
        try:
            counts, bins, patches = self.histogram
        except Exception:
            raise AttributeError('Before calling scale_data_from_hist() please'
            ' call hist_and_best_fit() to generate')
            
        ### Get current mean of curve or histogram
        if self.best_fit and try_curve:
            oldmean=self.fit_mean
        else:
            bincenters=get_bin_points(bins, position='c')            
            oldmean=hist_max(counts, bincenters)[1]

        ### Scale count_results by new scale
        scale=1.0 + ( (newmean - oldmean) / (oldmean) )
        self.count_results[attstyle]=self.count_results[attstyle]*scale
        self.uncorrected_dmean=oldmean
        
        ### Regenerate histogram
        try: #Returns filepath of histogram
            return self.hist_and_bestfit(attstyle=attstyle, **histbestfit_kwargs)
        except Exception as E:
            raise Exception('Failed to adjust histogram/guassian: %s',E)

    ### Methods to output results
    def full_summary(self):    
        o=open(self.summary_out, 'w')

        sumout= self._summary_header('#### Results Summary ####', self.sample_parms)
        inpout=  self._summary_header('\n\n#### Input parameters####', self.input_parms)
        imout= self._summary_header('\n\n#### Image parameters####', self.image_parms)
        partout= self._summary_header('\n\n#### Particle analysis/counting parameters####',\
                                      self.particle_analysis_parms)
        cov_out=self._summary_header('\n\n#### Coverage parameters####',self.coverage_parms)
        np_out=self._summary_header('\n\n#### NP Sizing parameters####', self.np_size_parms)
        prot_out=self._summary_header('\n\n#### Protein parameters####', self.protein_parms)

        o.write(sumout+imout+partout+inpout+cov_out+np_out+prot_out)     
        o.close()

    def special_summary(self, delim='\t', with_header=False, style='full'):
        ''' Custom summary method.  Outputs all releveant class attributes into a spreadsheet,
        then grouped summary files.  For example, one file just for image parameters, one file
        in regard to size estimations.  One for coverage and bsa binding.  Very adhoc and only
        useful for me (Adam Hughes) in my research probably.  With header is important for
        integration with mainscript.py'''     

        ### Don't forget, necessary to include filename first
        if style.lower()=='full':
            outparms=self.image_parms +self.input_parms + self.sample_parms + \
                self.particle_analysis_parms + self.coverage_parms+ \
                self.np_size_parms + self.protein_parms

        ### Essential parameters, coverage, nps, bsa, sizing
        elif style.lower() == 'lite':
            if self.xhismax:
                dout = r2(self.xhismax)
            else:
                dout = 'None'

            outparms=(
                      ('Image', self.shortname),                
                      ('NPS', '%.2e' % self.np_total_corrected),                      
#                      ('anal_part_error',r2(self.particle_fitting_error)),                      

                      # Particle equivalents; no noise
                      ('single_eqvs', r2(100.0 * float(self.single_counts) / self._np_total_equiv_nonoise)),
                      ('double_eqvs', r2(100.0 * float(self.double_particle_equiv) / self._np_total_equiv_nonoise)),
                      ('flat_eqvs',  r2(100.0 * float(self.flat_particle_equiv) / self._np_total_equiv_nonoise)),
                      ('super_eqvs', r2(100.0 * float(self.super_particle_equiv) / self._np_total_equiv_nonoise)),
                      ('Diam Est(%s)'%self.UNITS, dout), 
                      ('bw_nonoise(%)',r2(self.noiseless_bw_coverage))                      
                    )
            
            # XXX: Total hack for texorate
        elif style.lower() == 'lite_part_2':
            outparms=(
                      ('Image', self.shortname),                
                      ('BSA', '%.2e' % self.bsa_total),

                      # Actual particle counts; no noise
                      ('single_true',r2(100.0* float(self.single_counts) / self._np_total_actual_nonoise)),
                      ('double_true' ,r2(100.0* float(self.double_particle_actual) / self._np_total_actual_nonoise)),               
                      ('flat_true', '%.2e' % (100.0 * float(self.flat_particle_actual) / self._np_total_actual_nonoise)),
                      ('super_true', '%.2e' % (100.0 * float(self.super_particle_actual) / self._np_total_actual_nonoise)),
                      ('corr_cov(%)',r2(self.mean_corrected_coverage)),   
                      ('hex_ffrac(%)',r2(self.fillfrac_hexagonal * 100.0))
                      
                    )
            
            
            #XXX Add some additional parameters related to npsize estimate
           # outparms=outparms+self.np_size_parms

        ### Detailed coverage, particles, proteins, sizing
        elif style.lower()=='detailed':

            ### GLITCH CAN'T ADD (X,Y) + ((Z, B), (A,C)) CORRECTLY...
            ### WORKAROUND
            outparms=(('Filename', self.shortname), ('junk', 'junk'), ('thresholding', self.adjust))
            outparms=outparms+self.coverage_parms+\
                self.particle_analysis_parms_lite +  self.protein_parms_lite
            outparms=list(outparms)
            outparms.pop(1)
            outparms=tuple(outparms)
            outparms=outparms+self.np_size_parms
            


        else:
            raise AttributeError('Style keyword must be full, lite, or detailed \
            but %s was entered'%style)

        outstring=''
        if with_header:
            outstring=outstring+'#'+delim.join(item[0] for item in outparms) 

        outstring=outstring+'\n'+delim.join([str(item[1]) for item in outparms])
        return outstring    

    ### Private methods ###        
    
    def _summary_header(self, header, nested_tuple):
        ''' Used to expedite return process in summary file '''
        firstline='\t'.join(parm[0] for parm in nested_tuple)
        secondline='\t'.join(str(parm[1]) for parm in nested_tuple)
        return header+'\n'+firstline+'\n'+secondline


    def _find_nearest(self, array, value):
        '''Find nearest value in an array, return index and array value'''
        idx=(np.abs(array-value)).argmin()
        return idx, array[idx]       

#if __name__ == '__main__':	
    #image=ImageDestroyer('/home/glue/Dropbox/FiberData/August/AnalysiScriptTest/f3_9490.tif', \
                            #9490, 'home/glue/Dropbox/Fiberdata/August/AnalysiScriptTest/Test')
    ##  print image.count_results
