================
NpSurfaceCounter
================

This is a legacy script for counting  nanoparticles on optical fibers from SEM
images used at GWU. It is being supplanted by the ``AuNPModel`` script in pyparty_.
It is unlikely that the entire script will be migrated; however, because there's 
just too much nuance to start mucking with.  What I probably will change is IO
and CONFIG to make it more accessible, as well as possible change the thresholding
style if there's time for that.

   .. _pyparty : https://github.com/hugadams/pyparty

========
Workflow
========

Checkout out **EXAMPLE_RESULTS** folder to see if the types of output is 
useful for your project.  If

This is our ad-hoc workflow that this script inentionally was built for.  It assumes
a very particular directory structure, in particular that folders arranged by magnificaiton

Root ---> 50000 ---->  Image1, Image2 etc...

FINISH HERE... REALLY NEED TO GET RID OF IMAGEJ DEPENDENCE, SERIOUSLY

You can always ask me directly to help analyze your images if for whatever reason,
this script is useful to you.  hughesadam@gmail.com


About the Author
================

I'm a PhD student at GWU (check me out on researchgate_ and Linkedin_) and former Enthought intern. 
I work in biomolecule sensing and nanophotonics.   Like any PhD student, my time 
is stretched across many projects.  As such, the ``pyparty`` source code may is 
messy in places, and a test suite has yet to be developed yet.  Developing the 
iPython notebook tutorials alongside the code helped served as a basic test 
platform.  

   .. _researchgate : https://www.researchgate.net/profile/Adam_Hughes2/?ev=hdr_xprf
   .. _Linkedin : http://www.linkedin.com/profile/view?id=121484744&goback=%2Enmp_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1&trk=spm_pic
