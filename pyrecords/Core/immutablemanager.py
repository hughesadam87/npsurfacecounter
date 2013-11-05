from abstractmanager import AbstractManager
from collections import namedtuple

class ImmutableManager(AbstractManager):
    ''' Class used to shell out mutable or immutable typedchecked records.'''
    
    def __init__(self, *args, **kwargs):
        super(ImmutableManager, self).__init__(*args)
        self.verbose=kwargs.pop('verbose', False)       

        ### If mutable, return named tuple; otherwise, return object subclass
        vars(self)[self.typename]=namedtuple(self.typename, self.strict_fields.keys(), verbose=self.verbose)  #Creates a namedtuple class 

    def _make_return(self, args):
        return vars(self)[self.typename]._make(args)  #Return named tuple
    
    def _dict_return(self, kwargs):
        return vars(self)[self.typename](**kwargs)
        

if __name__ == '__main__':	
    personfields=[
        ('name',str('unnamed') ), ('age',int() ), ('income',float() )
                  ]
    ### Construct the class builder ###
    personmanager=ImmutableManager('Person', personfields)

    ### Get some people ###
    print '\nLets make some people\n'
    bill=personmanager._make(['Billy Gundam', 80, 10000.00])
    jill=personmanager._make(['Jill Blanks', 35, 15000.00])
    glue=personmanager._make(['glue', 32] )
    print bill
    print jill
    print glue


    print '\nThese are all still of type namedtuple, so all the builtin methods work\n'
    print '\nConversion to dictionary with _asdict()\n'
    print glue._asdict()
    print '\nNew named tuple with Field Replacement\n'
    print glue._replace(name='Not sara')

    ### TO MAKE: Let class take in keyword args to make objects from dict (mimicing **d), maybe
    ### may have to settle doing this from a new method like personmanager.fromdict()

    print '\nI can still subclass the namedtuple; although, now it defaults back to a namedtuple.  Extra \\\
    methods for subclassing need to be incoprorated.  Something like personmanager.subclass.\n'
    SuperPerson=namedtuple('SuperPerson', personmanager.Person._fields+ ('height', 'weight') )
    sara=SuperPerson('Sara Jenkins', 32.3, 32000, '6feet', '150lbs')
    print sara

    print '\nI can still refer directly to the class itself, which is sometimes necessary.  For example, \
           if I want to directly instantiate from a dictionary with **d notation.  Although, now defaults \
           and fields are nolonger enforced.\n'
    mydict={'name':'Jason', 'age': 30, 'income':4.0}
    jason=personmanager.Person(**mydict)
    print jason

    print '\nIf I want to pass a dictionary AND have it typechecked, there is a new method for that called \
          dict_make.  Note that the dictionary was incomplete and the default record value was returned instead\
          of returning an error!'
    freddict={'name':'Fred', 'age':32}
    fred=personmanager.dict_make(**freddict)
    print fred

    print '\nIf I tried to instantiate a named tuple directly with an incomplete dictionary, I would get an error'
    try:
        fred=personmanager.Person(**freddict)
    except TypeError:
        print 'Yup I just errored big time'    
