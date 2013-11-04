''' Data models for various aspects of npsurfacecounter. 
    Replace all pyrecords instances eventually, as well as sumary stuff 
    in imkclass'''

def r2(x):
    if x is None:  
        return 'None'
    return str(round(x,2))

class TexModel(object):
    ''' Store various attributes from imk_class temporarily.
        This is more memory efficient than accessing object directly, and not
        all of htese image paths are stored as attributes.
    '''
    
    image_path = '' #Etiher full image or cropped file
    hist_path1 = ''
    hist_path2 = ''
    
    # Imbuster coverage params
    bw_coverage = None
    corr_coverage = None 
    hex_ffrac = None
    
    def set_from_imbuster(self, obj):
        ''' Sets relevant coverage params from imbuster object.'''
        
        self.bw_coverage = obj.noiseless_bw_coverage
        self.corr_coverage = obj.mean_corrected_coverage
        self.hex_ffrac = obj.fillfrac_hexagonal * 100.0
        
    def as_tex_string(self):
        ''' Returns coverage params texorated string, rounded.'''
    
        bwmessage = r'BW coverage: {\bf %s}' % r2(self.bw_coverage)
        corrmessage = r'corr coverage: {\bf %s}' % r2(self.corr_coverage)
        ffmessage = r'hex fillfrac: {\bf %s}' % r2(self.hex_ffrac)      
        
        return '%s \;\; %s \;\; %s' % (bwmessage, corrmessage, ffmessage)