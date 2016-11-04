#==============================================================================
#RUN ALL  - STROMATOLITES
#==============================================================================

import os, time, subprocess, yaml

#tic
start_time = time.time()

#load configuration file
with open('./config', 'r') as config_yaml:
    config = yaml.load(config_yaml)

#load credentials file
with open('./credentials', 'r') as credential_yaml:
    credentials = yaml.load(credential_yaml)

#INITALIZE THE POSTGRES TABLES
print 'Step 1: Initialize the PSQL tables ...'
subprocess.call('./setup/setup.sh', shell=True)
os.system('python ./udf/initdb.py')

#BUILD THE BIBLIOGRAPHY
print 'Step 2: Build the bibliography ...'
os.system('python ./udf/buildbib.py')

#FIND TARGET INSTANCES
print 'Step 3: Find stromatolite instances ...'
os.system('python ./udf/ext_target.py')

#FIND STRATIGRAPHIC ENTITIES
print 'Step 4: Find stratigraphic entities ...'
os.system('python ./udf/ext_strat_phrases.py')

#FIND STRATIGRAPHIC MENTIONS
print 'Step 5: Find stratigraphic mentions ...'
os.system('python ./udf/ext_strat_mentions.py')

#CHECK AGE - UNIT MATCH AGREEMENT
print 'Step 6: Check age - unit match agreement ...'
os.system('python ./udf/ext_age_check.py')

#DEFINE RELATIONSHIPS BETWEEN TARGET AND STRATIGRAPHIC NAMES
print 'Step 7: Define the relationships between stromatolite phrases and stratigraphic entities/mentions ...'
os.system('python ./udf/ext_strat_target.py')

#DEFINE RELATIONSHIPS BETWEEN TARGET AND DISTANT STRATIGRAPHIC NAMES
print 'Step 8: Define the relationships between stromatolite phrases and distant stratigraphic entities/mentions ...'
os.system('python ./udf/ext_strat_target_distant.py')

#FIND BEGINNING OF REFERENCE LIST
print 'Step 9: Delineate reference section from main body extractions ...'
os.system('python ./udf/ext_references.py')

#BUILD A BEST RESULTS TABLE OF STROM-STRAT_NAME TUPLES
print 'Step 10: Build a best results table of strom-strat_name tuples ...'
os.system('python ./udf/ext_results.py')

#FIND ADJECTIVES DESCRIBING STROM
print 'Step 11: Find adjectives describing strom target words ...'
os.system('python ./udf/ext_target_adjective.py')


#summary of performance time
elapsed_time = time.time() - start_time
print '\n ###########\n\n elapsed time: %d seconds\n\n ###########\n\n' %(elapsed_time)
