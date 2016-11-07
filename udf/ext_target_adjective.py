#==============================================================================
#TARGET ADJECTIVE EXTRACTOR
#==============================================================================

# import relevant modules and data
#==============================================================================
import time, random, re, yaml, psycopg2
from psycopg2.extensions import AsIs

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

#IMPORT TARGETS WITH DEPENDENTS
cursor.execute("""
    SELECT docid, sentid, target_id, target_word, target_children
    
    FROM target_instances
    WHERE target_children<>'[[]]'; 
""")

target=cursor.fetchall()


#IMPORT THE SENTENCES DUMP
cursor.execute("""
    WITH temp as (
            SELECT DISTINCT ON (docid, sentid) docid, sentid
		     FROM target_instances
            WHERE target_children<>'[[]]'     
    )


    SELECT s.docid, s.sentid, words, poses
    FROM %(my_app)s_sentences_%(my_product)s AS s

	JOIN temp ON temp.docid=s.docid AND temp.sentid=s.sentid; 
    """, {
    "my_app": AsIs(config['app_name']),
    "my_product": AsIs(config['product'].lower())
    })

sentences=cursor.fetchall()

#initalize the target_instances table
cursor.execute("""
    DELETE FROM target_adjectives;
""")

#push drop/create to the database
connection.commit()


adj=[]
for idx,line in enumerate(target):
    docid, sentid, target_id, target_word, target_children = line
    target_children = eval(target_children)
    target_children =target_children[0]
    
    sent = [elem for elem in sentences if elem[0]==docid and elem[1]==sentid]
    
    for c in target_children:
        if sent[0][3][c]=='JJ':
            adj.append([docid, sentid, target_id, target_word, sent[0][2][c]])
            
            #write to PSQL table
            cursor.execute(""" 
                INSERT INTO target_adjectives(   docid,
                                                sentid,
                                                target_id,
                                                target_word,
                                                target_adjective)
                VALUES (%s, %s, %s, %s, %s);""",
                (docid, sentid, target_id, target_word, sent[0][2][c])
            )
        if c<0:
            print 'something is up!'

#push insertions to the database
connection.commit()
            
#close the connection
connection.close()
