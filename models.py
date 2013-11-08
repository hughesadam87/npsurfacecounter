''' Data models for various aspects of npsurfacecounter. 
    Replace all pyrecords instances eventually, as well as sumary stuff 
    in imkclass'''

def r2(x):
    if x is None:  
        return 'None'
    return str(round(x,2))

class TexModel(object):
    ''' Store various attributes from imk_class, as well as file paths from
        main_script output. Used by tex-generating functions.
    '''
    
    image_path = '' #Etiher full image or cropped file
    hist_path1 = ''
    hist_path2 = ''
    adjust_path = ''
    bright_path = ''
    
    adjust = None
    folder = None  #Folder shortname that image located in
    
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
        ''' Returns several parameters as r2-rounded string, separated
            by " \;\; " (ie 2 spaces in latex).'''
    
        bwmessage = r'BW coverage: {\bf %s}' % r2(self.bw_coverage)
        corrmessage = r'corr coverage: {\bf %s}' % r2(self.corr_coverage)
        ffmessage = r'hex fillfrac: {\bf %s}' % r2(self.hex_ffrac)  

        if self.adjust:
            adjmessage = r'man-adjustment: {\bf \color{blue}{Yes}'
        else:
            adjmessage = r'man-adjustment: {\bf \color{red}{No}'
            
        return ' \:\: '.join([bwmessage, corrmessage, ffmessage, adjmessage])
