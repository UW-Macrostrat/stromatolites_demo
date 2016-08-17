#==============================================================================
#DEFINE BEGINNING OF REFERENCES SECTION
#==============================================================================

#==============================================================================
# ACQUIRE RELEVANT MODULES and DATA
#==============================================================================

import time, random, psycopg2, yaml, re
import numpy as np
import matplotlib.pyplot as plt

from psycopg2.extensions import AsIs

#tic
start_time = time.time()

# Connect to Postgres
with open('./credentials', 'r') as credential_yaml:
    credentials = yaml.load(credential_yaml)

with open('./config', 'r') as config_yaml:
    config = yaml.load(config_yaml)

# Connect to Postgres
connection = psycopg2.connect(
    dbname=credentials['postgres']['database'],
    user=credentials['postgres']['user'],
    host=credentials['postgres']['host'],
    port=credentials['postgres']['port'])

cursor = connection.cursor()

doc_cursor=connection.cursor()
target_cursor=connection.cursor()
strat_cursor = connection.cursor()
sent_cursor = connection.cursor()


#==============================================================================
# FIND REFERENCE SECTIONS
#==============================================================================


#list of docids with orphaned targets
doc_cursor.execute("""
    SELECT docid FROM strat_target
    UNION
    SELECT docid FROM strat_target_distant
""")

refs=np.zeros(0,dtype={'names':['docid','sentid','type','depth'],'formats':['|S100','i4','|S100','f4']})
best_refs=np.zeros(0,dtype={'names':['docid','sentid','type','depth'],'formats':['|S100','i4','|S100','f4']})

for idx, doc in enumerate(doc_cursor):
    tmp_refs=np.zeros(0,dtype={'names':['docid','sentid','type','depth'],'formats':['|S100','i4','|S100','f4']})
    #collect the words between strat_phrases and orphaned target
    sent_cursor.execute(""" 
            SELECT docid, sentid, words from %(my_app)s_sentences_%(my_product)s
                WHERE docid=%(my_docid)s;""",
                {
                  "my_app": AsIs(config['app_name']),
                  "my_product": AsIs(config['product'].lower()),
                  "my_docid": doc[0],
                    })
                    
    
    for idx2, sent in enumerate(sent_cursor):
        docid,sentid,words = sent
        phrase = ' '.join(words)
        if words[0]=='References' or words[0]=='REFERENCES':
            tmp_refs = np.append(tmp_refs,np.array([(docid,sentid,'ref',0)],dtype=tmp_refs.dtype))
            
        if words[0]=='Bibliography' or words[0]=='BIBLIOGRAPHY':
            tmp_refs = np.append(tmp_refs,np.array([(docid,sentid,'ref',0)],dtype=tmp_refs.dtype))
        
        if words[0]=='Bibliographie' or words[0]=='BIBLIOGRAPHIE':
            tmp_refs = np.append(tmp_refs,np.array([(docid,sentid,'ref',0)],dtype=tmp_refs.dtype))

        if 'REFERENCES' in words:
            tmp_refs = np.append(tmp_refs,np.array([(docid,sentid,'ref_mention',0)],dtype=tmp_refs.dtype))

        if 'Acknowledgements' in words or 'Acknowledgments' in words or 'ACKNOWLEDGEMENTS' in words or 'ACKNOWLEDGMENTS' in words:
            tmp_refs = np.append(tmp_refs,np.array([(docid,sentid,'ack',0)],dtype=tmp_refs.dtype))

    if len(tmp_refs)==0:
        tmp_refs = np.array([(docid,0,'none',0)],dtype=tmp_refs.dtype)
    
    tmp_refs['depth']=tmp_refs['sentid']/(idx2+1.)    
    refs = np.append(refs,tmp_refs)
    tmp_refs=np.sort(tmp_refs,order='sentid')
    best_refs = np.append(best_refs,tmp_refs[-1])


#arbitrary cutoff for 'good' inferences
best_refs['sentid'][best_refs['depth']<0.1]=0
best_refs['type'][best_refs['depth']<0.1]='none'
best_refs['depth'][best_refs['depth']<0.1]=0.0

zeros = best_refs[best_refs['sentid']==0]
elapsed_time = time.time() - start_time


#%%

#NEW RESULTS TABLE
cursor.execute("""
    DROP TABLE IF EXISTS refs_location CASCADE;
    CREATE TABLE refs_location(
        docid text,
        sentid int,
        type text,
        depth real);
""")
connection.commit()

for row in best_refs:
    cursor.execute("""
    INSERT INTO refs_location(    docid,
    				sentid,
    				type,
    				depth)
    VALUES (%s, %s, %s, %s);""",
    (row['docid'],str(row['sentid']),row['type'],str(row['depth']))
    )
     


cursor.execute(""" UPDATE strat_target
                        SET refs_loc = refs_location.sentid
                        FROM refs_location
                        WHERE strat_target.docid = refs_location.docid

""")

cursor.execute(""" UPDATE strat_target_distant
                        SET refs_loc = refs_location.sentid
                        FROM refs_location
                        WHERE strat_target_distant.docid = refs_location.docid
""")

cursor.execute(""" UPDATE strat_target
                        SET in_ref = 'yes'
                        WHERE sentid > refs_loc
                        AND   refs_loc <>0

""")

cursor.execute(""" UPDATE strat_target_distant
                        SET in_ref = 'yes'
                        WHERE sentid > refs_loc
                        AND   refs_loc <>0

""")



connection.commit()

#%%

#tmp_refs=best_refs[(best_refs['sentid']!=0)]
#
#tmp = tmp_refs[np.random.choice(len(tmp_refs), 1)]
#
#my_sentid= np.arange(tmp['sentid']-4,tmp['sentid']+20)
#
#sent_cursor.execute(""" 
#        SELECT docid, sentid, words from %(my_app)s_sentences_%(my_product)s
#            WHERE docid=%(my_docid)s
#            AND   sentid = ANY(%(my_sentid)s)
#            ORDER BY sentid;""",
#            {
#              "my_app": AsIs(config['app_name']),
#              "my_product": AsIs(config['product'].lower()),
#              "my_docid": tmp['docid'][0],
#              "my_sentid": (list(my_sentid),)
#                })
#
#phrase=''                
#for idx2, sent in enumerate(sent_cursor):
#    docid,sentid,words = sent
#    words = ' '.join(words)
#    
#    if sentid==tmp['sentid']:
#        flag=words
#        phrase = phrase+'\n*****  '+words
#    else:
#        phrase = phrase+'\n-'+words
##    print words
#    
##    if sentid==tmp['sentid']:
#        
#        
#print '\n ###########\n\n %s \n\n ###########\n\n %s \n\n ###########\n\n' %(phrase,flag)

