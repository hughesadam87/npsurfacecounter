from config import ImmutableManager, from_file

#####################################################################################
## Defines basic fields and instantiates an immutable record type for storing data ##
#####################################################################################

### Real simple field for 2-column greyscale data from ImageJ's native histogram
grey_fields=( 
             ('pix_intensity', int(0) ), #0-256 bins basically
             ('count', int(0) )  
            )

### Define my fields, types and default values in one go, all of which are passed to the record manager
imagej_fields=( ('mag',int(0)),  #Image magnification
                ('rsmall',0.0), #Lower limit of radius parameter (any to account for INIFNITY)
                ('rlarge', 'Infinity'), #Upper limit of radius parameter any() IS A FUNCTION NOT A TYPE!
  #              ('rlarge', 15000.0),
                ('csmall',0.0), #Lower limit of particle circularity
                ('clarge',1.0),  #Upper limit of particle circularity
                ('despeckle',bool(False)), #Despeckle image after adjusting threshold
              )

results_fields=( ('thecount', int(0)),     #All of these are basically floats.  Uses thecount so no name conflicts with "count"methods in pandas
                 ('area',float(0) ),
                 ('mean',float(0) ),  #Mean grey scale value
                 ('stddev',float(0)  ),
                 ('mode',float(0) ),
                 ('min',float(0)),
                 ('max',float(0)),
                 ('x', float(0)),
                  ('y', float(0)),
                  ('xm', float(0)),
                  ('ym', float(0)),                  
                 ('perim', float(0) ),
                 ('bx', float(0)),
                 ('by', float(0)),
                 ('width', float(0)),
                 ('height', float(0)),     
                 ('major', float(0) ),
                 ('minor', float(0) ),
                 ('angle', float(0) ),
                 ('circ',float(0)),
                 ('feret',float(0)),
                 ('intden', float(0)),
                 ('median', float(0)),
                 ('skew', float(0)),
                 ('kurt', float(0)),
                 ('perc_area', float(0)),  #% area
                 ('rawintden', float(0)),
                 ('slice', float(0)),    
                 ('feretx',float(0)  ),
                 ('ferety',float(0)  ),
                 ('feretang', float(0) ),
                 ('minfer', float(0) ),                    
                 ('ar', float(0)),
                 ('roundness', float(0)),
                 ('solidity', float(0)),                 
               )

### Create immutable class called DomainCDD that has strict typechecking
ij_manager=ImmutableManager('IJFields', imagej_fields)
results_manager=ImmutableManager('Results', results_fields)
grey_manager=ImmutableManager('GreyData', grey_fields)

if __name__ == '__main__':
    results=from_file(results_manager, 'f3_9490_stats_full.txt')
    areas, circs=[ (row.area, row.circ) for row in results]
