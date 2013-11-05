##### Utilities functions for operating on individual DomainCDD objects and dictionaries of tem.
##### Not type checked and argument names are kept intentionally generic to 
##### encourage reuse.
from operator import attrgetter, itemgetter
import re
from pandas import DataFrame

####################################################################################
###### Utilities to operate on a single mutable or immutable object ################
####################################################################################

def alter_field(obj, field, func, verbose=True):
    ''' Takes in a function (eg split('>')) and attempts to perform that on the data field passed in.
        May be worth breaking this down to two functions, one for immutable, one for mutable so I don't
        have to do this try statement every single iteration!
        
        For immutables like tuple, fget will raise an attributeerror, so most cases will fail automatically.'''
    fget=attrgetter(field)
    newval=func(fget(obj))  #Perhaps add a try statement
    try:
        setattr(obj, field, newval)  #If mutable, just set attribue (untested)   
    except AttributeError:
        obj=obj._replace( **{field:newval} )
        
    return obj
    
    
###################################
###### File IO utilities ##########
###################################
def from_file(manager, infile, skip_assignment=False, warning=False, parsecomments=True):
    ''' Take in CDD superfamilies file and creates dataobjects.  Requires RecordManager object passed 
    in as well. Note, parser only enforces that lines of
    the correct length are added (THIS IS LIMITING).  Types are automatically set.
    If skip_assignment is True, all typchecking is bypassed, and all fields will stay strings
    and never be covnerted to fields.  This is useful only if you're analysis doesn't mind that 
    every field is a string!'''
         
    lines=open(infile, 'r').readlines()
    if parsecomments:  #MAY WANT TO JUST REPLACE WITH WITH A SKIP HEADER OPERATION, LESS MEMORY INTENSIVE
        lines=(row for row in lines if not re.match('#', row))
        
    lines=(row.strip().split() for row in lines if len(row.strip().split())==len(manager.strict_fields) )
               
    if skip_assignment:
        return tuple([manager._make_return(line) for line in lines])
    return tuple([manager._make(line, warning=warning) for line in lines])

####### Utilities designed for dictionary of DomainCDD objects 
####### (not type checked; terminology purposly generic) 
def sortbyarg(dic, *valuefields):
    ''' Enter list of fields/attribes to sort by.  For multiple field, will sort
      in order of entry.  All values in dictionary must have attributes corresponding to these fields.
      expects a dictionary of DomainCDD objects but should work in general.'''
    return tuple(sorted(dic.values(), key=attrgetter(*valuefields)))   

def to_dataframe(iterable, *attrfields):
    ''' If user specifies fields, only those fields, in that order, will be cast into a data frame.  Otherwise,
    fields are taken from first element in iterable.  Fields must be a list of strings.'''
    if attrfields:
        columns=attrfields #Empty dataframe of fixed column/row size

    ### The autoassign below only works for namedtuples (uses _fields attribute) and takes from the iterable[0] entry ###
    else:
        try:
            columns=iterable[0]._fields  #FOR NOW ONLY WORKS FOR NAMETUPLE attribute
        except AttributeError:
            raise AttributeError('to_dataframe requires a list of attributes')
        else:
            fget=attrgetter(*columns)
            items=[(idx, fget(v)) for idx, v in enumerate(iterable)]  #Key value pairs, key=index position, value =array of results
            return DataFrame.from_items(items, columns, orient='index') #Orient lets it know keys are for row indexing not 

### MAKE THESE WORK WITH DIC OR TUPLE!?!?

def sortbyitem(dic, *indicies):
    ''' Same as above but sorting by index'''
    return tuple(sorted(dic.values(), key=itemgetter(*indicies)))   

def get_field(dic, valuefield):
    ''' Returns all values of a single field/attribue (wrapper for attrgetter) as a tuple'''
    f=attrgetter(valuefield)
    return tuple([f(v) for v in dic.values()])

def get_fields(dic, *valuefields):
    ''' Returns all values of the *fields/attribue in a dictionary, keyed by attrname'''
    out={}
    for vfield in valuefields:
        out[vfield]=get_field(dic, vfield)  
    return out
    
def get_subset(dic, *valuefields, **kwargs):
    ''' Returns a new dictionary, with key and value fields defined by user.  There are
        to keyword args to this function (python 2.x doesn't allow variable neght *args and
        fixed keywords...)
        newkey: User can pass a field which will become the newkey to the dictionary.  
                If None, default keys of the original dictionary will be used.
        valuetype: kw to determine how values are contained (tuple, list, DomainsCDD)'''
    newkey=kwargs.pop('newkey', None)
    valuetype=kwargs.pop('valuetype', 'DomainsCDD')  #For now, this is not yet implemented.
    vget=attrgetter(*valuefields)        
    if newkey is None:
        return tuple( (k,vget(v) ) for k,v in dic.items() )  
    kget=attrgetter(newkey)    
    return tuple( (kget(v), vget(v))  for k,v in dic.items() )

def to_dic(iterable, *keyfields, **kwargs):
    ''' Take in an interable of manager return object, return a dictionary keyed by the specified field attribute.
        If more than one attribute is entered, then a unique key will be generated that is the concatenated attribute
        values separated by a the key_delimiter (this is done by using the get_unique_key method).  For example,
        if attribute field is name, then the name will simply be returned; however, if name and age are entered,
        something like "Bill_18 will be returned.'''
    key_delimiter=kwargs.pop('key_delimiter', '_')
    kget=attrgetter(*keyfields)    
    if len(keyfields) == 0:
        raise TypeError('to dic method requires attribute fields')
    elif len(keyfields) == 1:
        return dict((kget(v), v) for v in iterable)
    else:
        return dict( (key_delimiter.join([str(i) for i in kget(v)] ), v) for v in iterable) 


def histogram(cd_dic, *fields, **kwargs):
    ''' Returns count of unique occurrences for a field in CDDomain record.  Literally it is counting the
    occurrences of a unique attribute.  In practice, this is useful for understanding the domain distribution
    in the dataset.  Build to take in multple fields for flexibility.
    Keyword "sorted_return", if True, will sort the return in order of most to least'''
    sorted_return=kwargs.pop('sorted_return', False)
    reverse=kwargs.pop('reverse', True)  #If True, sorting is performed from greatest to least
    out={}
    for k, valuelist in get_fields(cd_dic, *fields).items():
        unique=list(set(valuelist))
        out[k]=[(v, valuelist.count(v)) for v in unique]
        if sorted_return == True:
            out[k].sort(key=itemgetter(1), reverse=reverse)  
        out[k]=tuple(out[k]) 
    return out    

### Following methods are for data filtering.  Most likely already built into database functionality like SQL ###
def filter_if(dic, **keyvals):
    ''' Iterate through dictionary, return entries if all passed attribute are equal.  For multiple
    attributes, can pass special keyword, "criteria" which can have values 'all' or 'any'.  
    If 'all', then all fields must be identical to retain object.  If 'any', then only one field must be.'''
    out={}
    criteria=kwargs.pop('criteria', 'all')
    vget=attrgetter(**keyvals)
    pass   #FINISH

def filter_by(dic, **keyvals):
    ''' Pass numerical attributes in, will return all values that meet the 'criteria'.  The filter
    criteria keywords are "equal", "lessequal", "less", "greaterequal", "greater" '''
    validcrit=['equal', 'lessequal', 'less', 'greaterequal', 'greater']
    criteria=kwargs.pop('criteria', 'equal')
    if validcrit == 'equal':
        pass
    elif validcrit == 'lessequal':
        pass        
    elif validcrit == 'less':
        pass
    elif validcrit == 'greaterequal':
        pass
    elif validcrit == 'greater':
        pass    
    else:
        raise KeyError('Criteria messed up in filter_bny') #Replace later
    
def dic_to_file(dic, outfilename, delim='\t'):
    ''' Used to output a dictionary to a file whose values are iterables.  LATER MAKE IT BE ABLE TO TAKE IN 
    SINGLE VALUED VALUES SO IT WORKS FOR ITERABLES AND SINGLEVALUES.'''
    f=open(outfilename, 'w')
    for item in dic.items():
#        if type(value) == str:
 #           outstring=            
        outstring=key + delim + delim.join(value) + '\n'
        f.write(outstring)
    f.close() 