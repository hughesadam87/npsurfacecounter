from recordmanager import RecordManager

### This is an example of how to define fields.  In this case, we are defining real data field
### of protein domain data from biological research.  Format for entry is a tuple of tuples,
### where each tuple contains the field name followed by the default value.

domain_fields=(
	('Query',str()), ('u1',str()), ('Accession',str()), \ 
	('Hittype',str()), ('PSSMID',int()), \
     	('Start',int()), ('End',int()), ('Eval',float()), \
	('Score',float()), ('DomAccession',str()), \
     	('DomShortname',str()), ('Matchtype',str()), 
	('u2',str()), ('u3',str())  \
		)

### Create namedtuple class called DomainCDD that has strict typechecking
domain_manager=RecordManager('DomainCDD', domain_fields)
