### Abstract Manager class.  Defines the abstract interface as well as some common methods.  
### Inheriting subclasses include mutable and immutable managertypes.  Each of these
### will build a class template from which users will generate dataobjects.
from collections import OrderedDict

_boolean_states = {'1': True, 'yes': True, 'true': True,
                   '0': False, 'no': False, 'false': False}     #Case insensitive

class AbstractManager(object):
    ''' Interface for creating mutable and immutable record managers.  Chose to do this so I can
        retain the most separation between immutable manager and mutable manager subclasses for 
    easier customization in the future. '''
    
    def __init__(self, typename, strict_fields):
        self.strict_fields=OrderedDict(strict_fields)
        self.typename=typename 
        
        ### Store field type and default information in varous formats for easy access by methods ###    
        ### Do these add a lot of memory overhead?###
        self._strict_names=[k for k in self.strict_fields.keys()]
        self._strict_types=[ type(v) for v in self.strict_fields.values() ]
        self.strict_defaults=[ v for v in self.strict_fields.values()]         
        self.totalfields=len(self.strict_defaults)
        
        ### CHECK TO SEE IF STRICT TYPES HAS EXOTIC FIELDS (FOR NOW JUST BOOLS), LATER WILL DETERMINE HOW KEYWORDS ARE PASSED ###
        
        self._has_bools=False  #For some reason, I need this line here!
        if bool in self._strict_types:
            self._has_bools = True

    def _typecheck(self, arg, fieldtype, warning=False):
        ''' Takes in an argument and a field type and trys to recast if necessary, then returns recast argument'''
        if not isinstance(arg, fieldtype):   
            try:
                oldarg=arg            #Keep for error printout
                arg=fieldtype(arg)    #Attempt recast
            except (ValueError, TypeError):  #Recast failed
                raise TypeError("Argument: %s to %s" % (arg, fieldtype))
            else:
                if warning:
                    print ("Recasting %s to %s as %s" % (oldarg, fieldtype, arg) )        
        return arg
    
    def _typecheck_withbools(self, arg, fieldtype, warning=False):
        ''' Similar to typecheck, except it has special support for boolean input.  Eventually, want to extend to
        other exotic imports.  I keep these methods separate because this will be slower.'''

        if not isinstance(arg, fieldtype):   
            try:
                oldarg=arg            #Keep for error printout
                if fieldtype == bool:
                    try:
                        arg=_boolean_states[arg.lower()]  #Remove case sensitivity   
                    except KeyError:
                        raise KeyError('A boolean value must be 1,0,true,false,yes,no, you entered %s\n') % arg
                else:
                    arg=fieldtype(arg)    #Attempt recast
            except (ValueError, TypeError):  #Recast failed
                raise TypeError("Argument: %s to %s" % (arg, fieldtype))
            else:
                if warning:
                    print ("Recasting %s to %s as %s" % (oldarg, fieldtype, arg) )        
        return arg        
        
    
    def _make_return(self, args):
        ''' Returns a custom object, either a namedtuple for immutable manager or a custom object for
        mutable manager'''
        pass
    
    def _dict_return(self, **kwargs):
        ''' Returns a custom object, either a namedtuple for immutable manager or a custom object for
        mutable manager'''        
        pass
    
    def _make(self, args, **kwargs):        
        '''Typechecks arguments and populates with defaults for non-entered fields.  Returns namedtuple. 
           The special keyword "warning" will make the _typecheck method alert the user of recasting.
           warning: If true and if recast is true, prints warning each time an input field is successfully type recasted.

           Another keyword "extend_defaults" can be used if the user wants to enter data of only a few fields.  For example,
           if the user passes in field 0, this will autofill field 1, field 2 etc.. with defaults.  This may not be a useful
           method since the dict_make method implements this robustly via keywords.  
           
           At the end, calls the "list return" or "dict_return" which will differ based on if the inheriting objects
           are mutable or immutable.'''                
        warning=kwargs.pop('warning', False)
        extend_defaults=kwargs.pop('extend_defaults', False)
        argslength=len(args) #So it isn't constantly computed
        
        if argslength != self.totalfields:
            if argslength > self.totalfields:  
                raise IOError('%s \nPlease enter %s fields, not %s, in class %s '\
                                 %(args, self.totalfields,argslength, self.typename ))  

            ### If not enough args entered, fill in with strict defaults ###
            else: 
                if extend_defaults==True: 
                    args=list(args) 
                    args.extend(self.strict_defaults[argslength:self.totalfields] )
                elif extend_defaults==False:
                    raise IOError('%s \nPlease enter %s fields, not %s, in class %s '\
                                     %(args, self.totalfields,argslength, self.typename ))
                else:
                    raise KeyError('extend_defaults keyword must be either True or False; you entered %s'%extend_defaults)

        ### Typecheck arguments ###
        if self._has_bools:
            for i in range(argslength):
                args[i]=self._typecheck_withbools(args[i], self._strict_types[i], warning)               
        else:
            for i in range(argslength):
                args[i]=self._typecheck(args[i], self._strict_types[i], warning)  #Will overwrite arguments as it goes
        return self._make_return(args)
        
    def dict_make(self, **kwargs):
        ''' User can pass a dictionary of attributes in and they will be typechecked/recast.  Similiar to passing
        dictionary directly to namedtuple using **d notation'''
        warning=kwargs.pop('warning', False)        

        for name, default in self.strict_fields.items():
            try:
                value=kwargs[name]
            except KeyError:
                kwargs[name]=default #Throw the default value in if missing
            else:
                value=self._typecheck(value, type(default), warning) #Typecheck if found
                kwargs[name]=value 

        return self._dict_return(kwargs)
