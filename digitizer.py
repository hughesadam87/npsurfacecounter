#-------------------------------------------------------------------------------
# Name: Digitizer
# Purpose: Used to easily store n-d arrays and bin them to a single bin spec
#          Very useful for example when comparing multiple data arrays in a histogram
# Author: Adam Hughes
# Created: 22/09/2012
# Python Version: EPD 7.3
#-------------------------------------------------------------------------------

from pandas import DataFrame, Series
import numpy as np
from collections import Counter
from math import sqrt, pi
from scipy.optimize import curve_fit
import matplotlib.mlab as mlab
from scipy.stats import norm
from numpy.random import shuffle as shuffitup

import logging
logger = logging.getLogger(__name__)
from logger import logclass

def digitize_by(df, digitized_bins, axis=0, avg_fcn='mean', weight_max=None):
    ''' Takes in an array of digitized bins, and then restructures a dataframe
    based on the bin array'''
    
    ### Map the digitized bins to series data with axis same as one that will be collapsed ###
    if axis == 0:
        mapped_series=Series(digitized_bins, index=df.index) #No, this isn't wrong, just weird
    else:
        mapped_series=Series(digitized_bins, index=df.columns)
    
    if len(df.shape)==1:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(mapped_series).mean()  #// is importanmt
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(mapped_series).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(mapped_series).mean()
            if weight_max:
                dfout= dfout.apply(lambda x: x / weight_max)  #These should be float division
            else:
                dfout= dfout.apply(lambda x: x/ x.max())
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)        
    
    elif len(df.shape)==2:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(mapped_series, axis=axis).mean()
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(mapped_series, axis=axis).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(mapped_series, axis=axis).mean()
            if weight_max:                
                dfout=dfout.apply(lambda x:x / weight_max, axis=axis)
            else:
                dfout=dfout.apply(lambda x: x / x.max(), axis=axis)            
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)

    else:
        raise NotImplementedError('df_rebin only works with 1-d or 2-d arrays')        
        
    return dfout       
    
    
def gauss(x, *p0):
    ''' Pass in best estimates for mu and sigma, it will use these as a starting curve
    and fit to data from np.curvefit function.
    
    p0 is two arguments, the estimates for starting mean and sigma.  Needed by least squares fit.
    Notation to be compatible with curve_fit requires this variable length argument notation.'''
    A, mu, sigma = p0
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

### Do I want this in the instance method????? ###
def hist_max(counts, bins, idx_start=0, idx_stop=None):
    ''' Finds the max bin index and value from the histogram.  Can pass indicies to drop so that 
    it can avoid '''
    if not idx_stop:
        idx_stop=len(counts)
    crange=counts[idx_start:idx_stop]
    countmax=max(crange)
    ### Ok here's trick.  Crange may be reduced, so I find the index of the max on that range.  This might be creducedmax=8
    ### but on my real range, this might be index 58, if idx start was 50.  Therefore, I add idx_start to the index 
    
    max_idx=np.where(crange==countmax)[0]
    if max_idx.shape[0] > 1:
        logger.warn('There are two bins in histogram that have idenitcal maxima and this might trip out gaussian autfit functions!  Using first one.')
    max_idx=max_idx[0]+idx_start
    binmax=bins[max_idx]
    return max_idx, binmax, countmax  #index of maximum, bin(x) value, count(y) value at max

def bin_above_below(series, left, right, height, shuffle=True):
    ''' Given a bin of width right-left, this splits the bin at given height.  
        The data corresponding to this bin (presumably in series) is evently distributed.
        For example, if the bin has 100 entries, and the height is 50, the data will be
        sliced into two regions.  One from 0-50 and one from 50-100, to be returned as 
        below and above respectively.
        
        kwds:
           series: Series of data presumably form which the bin was derived originally.
           left/right: start/stop of slice of series.
           height: y value up the bin.  If greater than the bin top, all data in the bin is returned
                   as "below".
           shuffle: Should data in series be randomized so as not to give any ordering 
                    bias when split between above, below.
           
        returns:
            Tuple of series (above, below) with the data from the original series partitioned between.
    '''
    if shuffle:
        shuffitup(series)  #In place operation
    
    height=int(round(height))
    sample=series[(series>=left)&(series<=right)] #Slice by values
    counts=len(sample)
    if height >= counts:
        below, above=sample, Series() #Empty series is easier for type checking in my use case

    else:
        below=sample.iloc[0:height] #just doing sample[] works too
        above=sample.iloc[height ::]

    return below, above

def range_slice(series, start, stop, style='value'):
    ''' Convienence wrapper to slice a single column of a df by either value or index.  Force user to specify
    to reduce possibility of error (aka pass integer when meant to pass float).'''
    
    if style=='index':
        start, stop=int(start), int(stop)
    elif style=='value':
        working=series.ix[series >= start]
        working=working.ix[working <= stop]         
    else:
        raise AttributeError('range slice can only slice by index or value, you passed %s'%style)
    return working

def fit_normal(counts, binpoints):
    ''' Fits a normal distribution to a histogram assuming the max of the histogram
    makes up the mean.  To fit with cropped data, pass cropped data into this.  For
    now this is incomplete and maybe not useful because it requires knowledge of 
    standard deviation as well.'''

    idx_max, mu, amp_at_mean=hist_max(counts, binpoints) #Skip first bin   

    ### Get the standard devation of a histogram
    ### Does not rely on original data at all
    std=data_from_histogram(counts, binpoints).std()
    
    ### Fit normal distribution at each point along binpoints array
    ### Scale it based on the max value of the histogram
    normal=mlab.normpdf( binpoints, mu, std)      
    scaleup=amp_at_mean / normal[idx_max]
    return normal*scaleup

def data_from_histogram(counts, binpoints):
    ''' Gets the standard devation from histogram data (binned by midpoint, not edges).
    Doesn't use real data at all.'''
    psuedo_data=[]    
    for i, point in enumerate(binpoints):
        psuedo_data=psuedo_data+ ( [point]*counts[i] ) #[1,1,1, + 2,2,2,2,2, + etc...]
    return np.array([psuedo_data])

### Probably deprecated, using wrong sigma and shit ###
def optimize_gaussian(counts, binpoints):
    ''' Takes in counts of a histogram and bin_midpoints (see get_bin_points function) and
    uses least squares regression to fit a guassian.
    
    Density counts is an array of weights, actual counts from np.histogram density=True'''
    mu, amp_at_mean=hist_max(counts, binpoints)[1:3] #Skip first bin
    sig=data_from_histogram(counts, binpoints).std()
    ### Make a best guest a initial params... [1.0, 0.0, 1.0] works fine ###
    p0=[amp_at_mean, mu, sig]
    coeff, var_matrix=curve_fit(gauss, binpoints, counts, p0=p0)
    hist_fit=gauss(binpoints, *coeff)

    fit_amp, fit_mean, fit_sig=coeff #Fit coefficients if you want to keep them
    return (hist_fit, fit_amp, fit_mean, fit_sig)
   
def psuedo_symmetric(counts, binpoints, idx_start=0, idx_stop=None):
    ''' Takes in a histogram, examines left edge to max, and then returns symmetric values
    as a pseudo-dataset. '''
    max_idx, x_mean, y_mean=hist_max(counts, binpoints, idx_start=idx_start, idx_stop=idx_stop)
    symrange=range(idx_start, (1+max_idx+(max_idx-idx_start) ))  #idx start ... idx mean ... idx start ... idx mean +1 (for symm)    
    symcounts=np.array([counts[data_idx] for data_idx in symrange])
    symbins=np.array([binpoints[data_idx] for data_idx in symrange])
    return symcounts, symbins
    

def get_bin_points(binarray, position='c'):
    ''' Takes in an array of bin edges (returned from histogram) as returned from a histogram
    and finds the values at the midpoints, left or right edges.  Useful when plotting a scatter 
    plot over bins for example.'''

    ### Return center xvalue of bins
    if position =='c':
        return (binarray[:-1] + binarray[1:])/2.0  #I don't quite understand this notation

    ### Return left edge xvalue of bins
    elif position =='l':
        return np.array([binarray[i] for i in range(len(binarray-1))])
    
    ### Return right edge xvalue of bins
    ### Note, bins are defined by their left edges, so this has to compute the bin width.
    ### Does so by looking at first two elements.  THEREFORE SPACING MUST BE EVEN!
    elif position =='r':
        width=binarray[1]-binarray[0]
        return np.array([binarray[i]+width for i in range(len(binarray-1))])
    
def df_rebin(df, binwidth, axis=0, avg_fcn='weighted', weight_max=None):
    ''' Pass in an array, this slices and averages it along some spacing increment (bins).
    Axis=0 means averages are computed along row.  axis=1 means averages are computed along column.
    Dataframe already handles most issues, such as if binning in unequal and/or binning is larger than 
    actual length of data along axis.  Aka bin 100 rows by 200 rows/bin.
    Binwidth is the spacing as in every X entries, take an average.  Width of 3 would be
    every 3 entries, take an average.
    
    Redundant because if series is passed in, the axis keyword causes errors.
    
    If using avg_fcn='weighted', one can pass an upper limmit into the "weight_max" category
    so that weighting is to a fixed value and not to the max of the dataset.  This is
    useful when comparing datasets objectively.  For dataframes, weight_max may be a 1d
    array of the normalization constant to each column in the dataframe.  If a single value
    is entered, or for a series, that value will be divided through to every row.
    
    Note: avg_fct='weighted' and weight_max=None will find a max after binning the data, 
    and divide all other column(or row values) by the max.  
    This is not the statistical normaization, which should be added later (X-u / sigma).'''


    if len(df.shape)==1:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(lambda x:x//binwidth).mean()  #// is importanmt
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(lambda x:x//binwidth).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(lambda x:x//binwidth).mean()  #Groupby uses int division
            if weight_max:
                dfout=dfout.apply(lambda x: x / weight_max)      #Apply uses float division
            else:
                dfout=dfout.apply(lambda x: x/ x.max())
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)        
    
    elif len(df.shape)==2:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).mean()
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).mean()
            if weight_max:                
                dfout=dfout.apply(lambda x:x / weight_max, axis=axis)
            else:
                dfout=dfout.apply(lambda x: x / x.max(), axis=axis)            
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)

    else:
        raise NotImplementedError('df_rebin only works with 1-d or 2-d arrays')        
        
    return dfout   

def get_binwidth(array, bin_number):
    ''' Calculates binwidth requried to maintain binnumber over this column/array.   Mostly left as its 
    own method in case this parameter is ever useful when working with data and curious about binwidth.'''
    vmin, vmax=array.min(axis=0), array.max(axis=0)
    return (vmax-vmin)/float(bin_number)       

def get_binadjustment(array, bin_number):
    ''' Given an array, this returns the proper adjusted bin array to maintain an identical bin number
    throughout this program.  Useful in case the bin adjustment or bin step are useful information.'''
    vmin, vmax=array.min(axis=0), array.max(axis=0)
    binstep=self._get_binwidth(array, bin_number)
    return np.arange(vmin, vmax, binstep) 


@logclass(log_name=__name__ , public_lvl='debug')
class MultiHistMaster(object):
    ''' Takes in multidimensional dataframe and a bin number.  It then digitizes all
    data columns equally along the bins.  Basically this means I can take multi-dimensional 
    field data (say areas, lengths, circularity of the same batch of particles) and bin it
    all to the same binwidth (computed internally).  Then I can do things like plot a histogram
    of area, and project circularity along the bins in the form of color mapping or shading.'''
    def __init__(self, dataframe=None, bin_number=None):
        self.df=dataframe
        if bin_number:
            self.bin_number=int(bin_number) #This an issue making this an int here?
        
    ### If application is going to make several calls to histogram builder, one can store
    ### the histogram of all the dd arrays at once in the dd_histogram_frame and digitized_Frame
    ### data frames.  If only making a few calls, can compute single histograms on the fly 
    ### with the single methods below.
    @property 
    def dd_histogram_frame(self):
        ''' Dataframe that actually stores a 1d histogram based on bin_number for each
        array in the dataframe.  If only want one at a time, can use the single hist method below'''
        histframe=DataFrame(columns=self.df.columns, index=[i for i in range(self.bin_number)] )
        for col in self.df.columns:
            histframe[col]=self.single_histogram(col)[0] #BIN OINFORMATION IS LOST!
        return histframe
        
    @property
    def digizied_frame(self):
        ''' This digitizes all columns in the digiframes using the same bin number.  Since
        digitizing requires bin arrays, this creates the correct bin array to make sure
        that all the digizied arrays have the same length.  If I only want one at a time
        use the single_digitize method below.'''
        digframe=DataFrame(columns=self.df.columns, index=self.df.index)
        for col in self.df.columns:
            digframe[col]=self.single_digitize(col)
        return digframe
    
    def single_digitize(self, column):
        ''' Column must be name of valid column in self.df frame.  Returns digitized version of it
        based after adjusting the correct bin width to fit this column.'''
        adjusted_bins=get_binadjustment(self.df[column], self.bin_number)
        return np.digitize(self.df[column].values, adjusted_bins)        
    
    def single_histogram(self, column):
        ''' 1d elements of histogram for column being a string pointing to name in dataframe column.'''                
        return np.histogram(self.df[column], self.bin_number)   

    def subset(self, *columns):
        ''' Subset of a dataframe, with optional sorting by column.'''
        return self.df.reindex(columns=columns)
         
    
    def digitized_weights(self, column, return_style):
        ''' Returns the digitized bin array as bin index vs. column value.  Returns a dictionary of 
        bin index:[values] for all values in that bin index.  return_style allows user to control
        how return is obtained.
        CAREFUL: DIGITIZED BINS START AT 1 NOT 0!!! I go ahead and corrected for this after!'''
        digidx=self.single_digitize(column)
        digidx=[i-1 for i in digidx]
        data=self.df[column].values
        zipped=zip(digidx, data) #(c1,bin1, c2,bin1, c3,bin2 ...)
        dic=dict((idx, [0.0]) for idx in range(0, self.bin_number))  #Empty dictionary of bin indicies bin1:[], bin2:[] with weight 0.0
        for idx, value in zipped:
            dic[idx].append(value)  #Populate dictionary bin1:[c1, c3, c30], bin2:[c2,c33,c22]        
    
        ### turn all value lists into numpy arrays to vectorize downstream operations
        for key in dic.keys():
            dic[key]=np.array(dic[key])

        ### Return bin:[c1, c2, c3...] for all points in bins
        if return_style.lower()=='verbose':
            return dic

        ### Return bin:[sum(c)]
        elif return_style.lower()=='summed':
            dic=dict((k, np.sum(v) ) for k,v in dic.items()) 

        ### Return bin:[sum(c)/len(c)]
        elif return_style.lower()=='averaged':
            dic=dict((k, (np.mean(v)) ) for k,v in dic.items()) 
            
        elif return_style.lower()=='normalized':
            vmax=max(np.sum(v) for v in dic.values()) #max bin in the histogram
            dic=dict((k, (np.sum(v)/vmax) ) for k,v in dic.items()) #since c is already scale of 0-1, average is already normalized

        else:
            raise NameError('return style trait must be averaged, summed, verbose, normalized not %s' %return_style.lower())

        return dic    
    
     
    def min_mode_max(self, column, vmin=None, vmax=None):
        ''' Return min, max and mode and counts of data in a column.  Vmin/vmax gives user option
        to specify a working range of the data column.  NOTE AUTO CONVERTS TO FLOATS TO MAKE SURE
        SLICING NOT DONE BY INDEX.'''
        working=self.df[column]
        if not vmin and not vmax:
            working.apply(lambda x: float(x))
        elif vmin and vmax:
            working=working[float(vmin):float(vmax)]  
        elif vmin and not vmax:
            working=working[float(vmin):] #One : not ::
        elif vmax and not vmin:
            working=working[:float(vmax)]  
        wcount=Counter(working)
        wmin=min(working)
        wmax=max(working)
        return ( (wmin, wcount[wmin]), wcount.most_common(1)[0], (wmax, wcount[wmax]) )        
    

    ### Following nmethods work on numpy arrays in general, so must pass self.df[column] as the argument.
    ### Moreso important in case user wants to probe the binwidth or binadjustment array that was used
    ### in calculating histograms or digitized stuff.
    
        
         
    
    def _set_binnumber_from_data_binwidth(self, column, binwidth):
        ''' I can instantiate the multihistmaster from a bin number; however, in some cases, we 
        prefer to fix it via a bin width (which depends on the values of hte data), and then choose 
        and set te bin number based on this.  Useful if you need the binnumber from the data, but
        didn't already instantiate this class (aka didn't put the data together).
        
        I made this because I had the binwidth from my area of a pixel, and wanted to compute binnumber
        without needeing to store the areas data apart from the data in this program.
        
        bw= range/#bins '''
        attr_range=abs(self.df[column].max() - self.df[column].min()) 
        self.bin_number=int( attr_range/binwidth )       
                
        
        
        
    
        
            
