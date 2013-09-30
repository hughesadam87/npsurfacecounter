from traits.api import *
from traitsui.api import *
import os, shutil
from image_K import main_go

class IMJ(HasTraits):
    indir=Directory()
    outdir=Directory( )
    parms_file=File('/home/glue/Dropbox/FiberData/August/AnalysiScriptTest/params.txt')
    parms_str=List
    sync_change=Button
    analyze=Button
    
    def _indir_default(self):
        #return os.getcwd()
        return '/home/glue/Dropbox/FiberData/August/AnalysiScriptTest/F1'

    def _outdir_default(self):
        #return os.getcwd()
        return '/home/glue/Dropbox/FiberData/August/AnalysiScriptTest/F1_RESULTS'
        
        
    
    def _parms_file_changed(self):
        try:
            f=open(self.parms_file, 'r')
        except IOError:
            self.parms_str=''
        else:
            lines=[]
            for line in f:
                lines.append(line)
            f.close()
            self.parms_str=lines

    ### FIX THIS SO THAT IT FIRST WRITES TO AN INTERMEDIATE FILE, THEN RENAMES ###
    def _sync_change_fired(self):
        ''' If use changes parameters in editor, this will overwrite file'''
        raise NotImplementedError('NOT IMPLEMENTED FOOL')
        #f=open('temp', 'w')
        #for line in self.parms_str:
            #f.write(line)
        #f.close()
        #shutil.copy('temp', self.parms_file)  
        
        
        
    def _analyze_fired(self):
        ''' Runs main script.  Overwrite turned off by default. '''
        main_go(self.indir, self.outdir, self.parms_file)
        
    traits_view=View(
                     Item('indir', label='Image Root Directory'),
                     Item('outdir', label='Output Directory'),
                     Item('parms_file', label='Parameters File'),
                     Item('parms_str', label='Parameters', style='custom', editor=ListStrEditor()),
                     HGroup(
                         Item('sync_change', label='Sync parms change', show_label=False), 
                         Item('analyze', label='Run Image Analysis', show_label=False)
                           ),
                     width=800, height=400, title='Image J Jacker'
                    )


if __name__ == '__main__':	
    IMJ().configure_traits()