from abstractmanager import AbstractManager
from collections import OrderedDict

class Mutable(object):
    ''' An object subclass with a few extra features. For one, it can be initialized directly from a dictionary
    of attributes with **dict.  Secondly, it has a __repr__ method to return a nicely formatted printout similar
    to the native one of namedtuple.  Very similar to the namedtuple of recordtype_2011 class.  Order is retained
    through how dictionaries are passed in through kwargs.'''

    def __init__(self, **kwargs):
        ''' Can initialize with dictionary of attribtues directly'''
        super(Mutable, self).__init__()
        self.ordered_fields=kwargs.keys()  #Because these are passed as an ordered dict, I retain attribute order.
        self.__dict__.update(kwargs)
        
    def _asdict(self):
        ''' To emulate nametuple method of returning an ordered dictionary.'''
        return OrderedDict([ (f, self.__dict__[f]) for f in self.ordered_fields])
        
    def __repr__(self):
        return self.__class__.__name__+ '(' + \
                 ', '.join('%s=%s'%(f, self.__dict__[f]) for f in self.ordered_fields) + ')'
        
    
class MutableManager(AbstractManager):
    ''' Creates a mutable python object subclass that stores attribtues such that they are mutable.
        'dict_make' method ensures typechecking and defaults before attribute setting.
        May add later support to have different containers rather than object subclasses. '''

    def __init__(self, *args, **kwargs):
        super(MutableManager, self).__init__(*args)
        ### Create a python object (MUTABLE) with attribute fields set to defaults ###
        vars(self)[self.typename]=type(self.typename, (Mutable,), self.strict_fields) 


    ######### FIX THIS ONE IT IS NOT IMPLEMENTED.  HOW DO YOU SET ARGUMENTS FROM LIST FOR OBJECT ####
    def _make_return(self, args):
        return vars(self)[self.typename](*args)  #Return named tuple
    #################################################################################################

    def _dict_return(self, kwargs):
        return vars(self)[self.typename](**kwargs)
    

if __name__ == '__main__':	
    personfields=(
        ('name',str('unnamed') ), ('age',int() ), ('income',float()), 
        ('jew',0.0), ('bret', 32.) ,
                 )
    ### Construct the class builder ###
    personmanager=MutableManager('Person', personfields)
    a=personmanager.Person()
    print a.name

    ### Get some people ###
    bill=personmanager.dict_make(name='bill', age=3.5, warning=True)
    print bill
    print bill._asdict()
    bill.name='joe'
    print bill
