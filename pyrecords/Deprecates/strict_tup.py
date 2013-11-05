from collections import namedtuple

strict_fields=[
     ('Query',str()), ('u1',str()), ('Accession',str()), ('Hittype',str()), ('PSSMID',int()), \
     ('Start',int()), ('End',int()), ('Eval',float()), ('Score',float()), ('DomAccession',str()), \
     ('DomShortname',str()), ('Matchtype',str()), ('u2',str()), ('u3',str())  
     ]

strict_names=[v[0] for v in strict_fields]
strict_types=[ type(v[1]) for v in strict_fields ]
strict_defaults=[ v[1] for v in strict_fields]

MyTuple= namedtuple('MyTuple', strict_names)

def _make(*args, **kwargs):
    '''Typechecks arguments and populates with defaults for non-entered fields.  Returns namedtuple. 
       Some special keywords to manipulate some of the behavior.  These are:
       verbose: Determine if named tuple is verobse upon creation.
       recast: If true, will attempt to recast poor input from user (aka int ---> float); however, will
               slow down the overall return time of the function, so may want the option to turn off.
       warning: If true and if recast is true, prints warning each time an input field is successfully type recasted.'''
    verbose=kwargs.pop('verbose', False)
    recast=kwargs.pop('recast', True)
    warning=kwargs.pop('warning', False)
    
    
    if len(args) > len(strict_defaults):
        raise ValueError('Too many arguments')
    ### If not enough args entered, fill in with strict defaults ###
    if len(args) < len(strict_defaults):
        args=list(args) 
        args.extend(strict_defaults[len(args):len(strict_defaults)] )       
    ### Typecheck arguments ###
    for i in range(len(args)):
        arg=args[i] ; fieldtype=strict_types[i]
        if not isinstance(arg, fieldtype):   
            try:
                arg=fieldtype(arg)
            except (ValueError, TypeError):  #Recast failed
                raise TypeError("Argument: %s to %s" % (arg, fieldtype))
            else:
                if warning:
                    print ("Recasting %s to %s" % (arg, fieldtype) )
    return MyTuple(*args)


if __name__ == '__main__':	
    a=_make("hi", "there")
    print a
    print a._fields
    print a._replace(Query=32)
    print a._asdict()