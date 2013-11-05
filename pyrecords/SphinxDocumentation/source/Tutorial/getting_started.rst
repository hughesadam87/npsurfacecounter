Getting Started
===============



Introduction to containers and records:
--------------------------------------

　

Good programs always start by managing data in a flexible and robust manner. Python has great builtin container datatypes (lists, tuples, dictionaries), but often, we need to go beyond these and create flexible data handlers which are custom-fitted to our analysis. To this end, the programmer really does become an architect, and a myriad of possible approaches are applicable. This is a double-edged sword, though, as inexperienced coders (like me) will tend to go down the wrong avenues, and implement poor solutions. Emerging from such a trajectory, PyRecords is an attempt to ease the suffering.

　

Immutable containers:
--------------------

As far as immutable containers go, Python already has a nice builtin type for managing records- the underused `namedtuple <http://docs.python.org/library/collections.html#collections.namedtuple>`_. A namedtuple is an immutable array container just like a normal tuple, except namedtuples have field designations. Therefore, elements can be accessed by attribute lookup and itemlookup (ie x.a or x[0]); whereas, tuples have no concept of attribute lookup. Namedtuples are a really great option for storing custom datatypes for these reasons:

* They are lightweight (take up very little memory).

* They are easily interfaced to file or sql database I/O, but also can be declared in-code.

* They have many basic builtin utilities for quick container transformations (nametuple to dict for example).

　

Mutable containers:
------------------

Probably most common way to build a new datacontainer is to subclass Python's builtin *object* subclass. A `great example <http://www.daniweb.com/software-development/python/code/216597/class-implements-a-structurerecord-python>`_ of this is available at daniweb. This is an example of a *mutable* class, since the data may be accessed and changed by setting attributes::

   ted = Employee()
   ted.name = 'Ted Tetris'

　

Shortcomings:
------------

There are three possible shortcomings one may incur when using these objects. These are:

#. These containers have no intrinsic understanding of default field values.
#. These containers have no intrinisic understanding of type.
#. The mutable and immutable containers explained above are vastly different in syntax and function; a unified framework needs to incorporate them freely.

　

I will demonstrate these shortcomings with an example. These examples will use the namedtuple (immutable container); however, are applicable to the object subclass.

　
.. sourcecode:: ipython

   In [1]: from collections import namedtuple

   In [2]: Person=namedtuple('Person', 'name, age, height')
   In [3]: bret=Person(name='bret', age=15, height=50)
   In [4]: bret

   Out[4]: Person(name='bret', age=15, height=50)




This is a nice record. I can access values by attribute lookup and I can use builtin methods to do nice things like return a dictionary without building any extra code.

　
.. sourcecode:: ipython
   In [5]: bret.age, bret.name, bret.height
   
   Out[5]: (15, 'bret', 50)

　

　
.. sourcecode:: ipython
   In [6]: bret._asdict()
   
   Out[6]: OrderedDict([('name', 'bret'), ('age', 15), ('height', 50)])

　

Ok, so this works nicely, but what if we want to read in records with no height column. *This is the first place that namedtuple will fail you.*

　
.. sourcecode:: ipython

   In [59]: ted=Person(name='ted', age=50)
   
   
HOW TO I MAKE THIS ERROR WORK   
---------------------------------------------------------------------------

TypeError Traceback (most recent call last)

<ipython-input-59-23acd5446d52> in <module>()

----> 1 ted=Person(name='ted', age=50)

TypeError: __new__() takes exactly 4 arguments (3 given)

　

There are many instances when it is desirable to have this behavior; however, there are also instances when it is not desirable. For example, if we were storing data input from a survey and certain fields were left blank, do we really want this to crash the program? The alternative is to populate this with null or default data manually, so wouldn't it be great if namedtuples understood this implicitly? One can think of many other instances where defaulting is important, and it is especially helpful when fields have very obscure or misleading dataypes, which may confuse anyone else using your codebase

The second thing namedtuples don't do is enforce field types. Consider again our Person class. The attribute "name" implies that a string should be entered, but there's nothing to enforce this. The same is true for height; that is, certain information is presumed on the user's part.

　
.. sourcecode:: ipython

   In [10]: kevin=Person(name=32, age='string input', height=['a', 'list', 'has been entered'])  
   In [11]: kevin
   
   Out[11]: Person(name=32, age='string input', height=['a', 'list', 'has been entered'])

　

Because a named tuple is a very basic container, it really doesn't care why types of objects you pass into the fields. Without getting into a philosophical argument on duck typing, I think we can all agree that there are times when this behavior is undesirable. Imagine you were going to share your codebase with someone else unfamiliar with the subject. Fieldnames might not be so obvious. Additionally, if you built your analysis assuming the height attribute had a very particular format, eg (6 foot 9 inches), everyone's life would be easier if the namedtuple new about it.

At the end of the day, I think all of these considerations fall under the umbrella of record keeping in Python. It is an interesting topic and certainly warrants `further discussion <http://www.artima.com/weblogs/viewpost.jsp?thread=236637>`_.

Let me illustrate how PyRecords works. Since the user knows the name and type of the fields ahead of time, he simply defines these in a nested tuple. This tuple is passed to one of the PyRecord classes, in this case, the immutablemanager class.

　
.. sourcecode:: ipython
   
   In [12]: from pyrecords.Core import ImmutableManager
   In [16]: personfields=[('name', 'unnamed',) , ('age', int()), ('height', float() )]
   
   In [17]: personmanager=RecordManager('Person', personfields)

　

Using this fairly innocuous syntax, we've just declared default values and types. Now, the *name* field knows that only string input is acceptable, and will default to *unnamed* if not explicitly entered. The *personmanager* class is built to seem like a namedtuple. For example, we can create objects from a list using the "_make" method, just like a namedtuple!

　　
.. sourcecode:: ipython

   In [26]: bill=personmanager._make('Billy', 32, 10000.00)   
   In [27]: bill
   
   Out[27]: Person(name='Billy', age=32, height=10000.0)

　

At first glance, this looks like no different from the standard namedtuple _make() method; however, this _make method() is being called on the ImmutableManager class; therefore, it will typecheck fields. We can make the typcechecking verbose with a keyword, "warning".

　
.. sourcecode:: ipython

   In [29]: jill=personmanagerjill=personmanager._make('Jill', 40.0, 50, warning=True)  
   Recasting 40.0 to <type 'int'> as 40   
   Recasting 50 to <type 'float'> as 50.0

   In [30]: jill
   
   Out[30]: Person(name='Jill', age=40.0, height=50)

　

Of course, certain types can't be recast, therefore, an error will come up showing exactly why.

　
.. sourcecode:: ipython

   In [31]: adam=personmanager._make('Adam', 'teststring', 40.0)
 
   Out[31]:TypeError: Argument: teststring to <type 'int'>

　

All of the returns are still namedtuples, so all standard methods natively work.

　
.. sourcecode:: ipython
   In [33]: bill._asdict()

   Out[33]: OrderedDict([('name', 'Billy'), ('age', 32), ('height', 10000.0)])

　

FINISH FROM FILE AFTER GETTING THIS TO WORK

　

　
