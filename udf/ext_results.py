#==============================================================================
#GENERATE RESULTS TABLE
#==============================================================================

import time, random, re, yaml, psycopg2, copy, csv
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


#NEW RESULTS TABLE
cursor.execute("""
    DROP TABLE IF EXISTS results CASCADE;
    CREATE TABLE results(
        target_id int,
        docid text,
        sentid int,
        target_word text,
        strat_phrase_root text,
        strat_flag text,
        strat_name_id  text,
        age_sum text,
        source text,
        phrase text,
        is_strat_name text DEFAULT 'yes',
        in_ref text
        );
""")
connection.commit()

#TMP RESULTS TABLE
cursor.execute("""
    DROP TABLE IF EXISTS results_new;
""")

#push drop/create to the database
connection.commit()

#gather results from the same-sentence inferences
cursor.execute(""" 
    INSERT INTO results (target_id, docid, sentid, target_word, strat_phrase_root,strat_flag,strat_name_id, age_sum, phrase, in_ref) 
		(SELECT target_id, docid, sentid,  target_word, strat_phrase_root,strat_flag,strat_name_id, age_sum, sentence, in_ref
				FROM strat_target 
				WHERE ((num_phrase=1 AND @(target_distance)<51) 
				OR   (target_relation='parent' AND num_phrase <8 AND @(target_distance)<51)
				OR   (target_relation='child'  AND num_phrase <8 AND @(target_distance)<51)))"""
)
  
#push insertions
connection.commit()

#mark these inferences as coming from same sentence
cursor.execute("""
    UPDATE results SET source='in_sent' WHERE source IS NULL 
   """
)

#push update
connection.commit()

#gather results from the near-sentence inferences
cursor.execute(""" 
    INSERT INTO results (target_id, docid, sentid, target_word, strat_phrase_root,strat_flag,strat_name_id, age_sum, phrase, in_ref) 
		(SELECT target_id, docid, sentid,  target_word, strat_phrase_root,strat_flag,strat_name_id, age_sum, words_between, in_ref
				FROM strat_target_distant 
				WHERE num_phrase=1)"""
)
  
#push insertions
connection.commit()

#mark these inferences as coming from near sentence
cursor.execute("""
    UPDATE results SET source='out_sent' WHERE source IS NULL 
   """
)

#remove non-unique rows
cursor.execute("""
    CREATE TABLE results_new AS (SELECT DISTINCT * FROM results)
   """
)


#adopt tmp results table
cursor.execute("""
    DROP TABLE results
   """
)

cursor.execute("""
    ALTER TABLE results_new RENAME TO results;
   """
)


#add serial primary key
cursor.execute("""
    ALTER TABLE results ADD COLUMN result_id serial PRIMARY KEY;
   """
)

#push updates
connection.commit()

#list of known and troublesome ligatures
weird_strings = [['\xef\xac\x82', 'fl'], ['\xef\xac\x81', 'fi']]


#IMPORT THE RESULTS - SIMPLE CHECK FOR STRAT NAME MENTION VALIDITY 
cursor_main = connection.cursor()
cursor_main.execute(""" SELECT * FROM results WHERE strat_flag = 'mention'; """)

test=[]

for line in cursor_main:
    #collect individual elements from the results dump
    target_id, docid, sentid, target_word, strat_phrase_root,strat_flag,strat_name_id, age_sum, source, phrase, mention_check, in_ref, result_id = line
    checked=[]
    
    #ligature replacement
    for ws in weird_strings:
        if ws[0] in phrase:
            phrase=phrase.replace(ws[0],ws[1])
    
    #find all mentions of strat_phrase_root
    matches=[m.start() for m in re.finditer(strat_phrase_root,phrase)]
    
    #loop through matches
    for m in matches:
        #lets look at the word that follows the potential strat name
        tocheck = phrase[m+len(strat_phrase_root)+1:]
        tocheck=tocheck.split(' ')
        
        #capitalized word following strat name mention invalidates it. Exceptions include:
            #1) end of sentence  2) Series  3) parantheses
        if tocheck[0].lower()!=tocheck[0] and tocheck[0]!='Series' and tocheck[0][0]!='.' and tocheck[0]!='-LRB-' and tocheck[0]!='-RRB-':        
            checked.append('no')
        else:
            checked.append('yes')
    
    #update post gres table
    if 'yes' not in checked:
        cursor.execute("""
            UPDATE results SET is_strat_name = %s WHERE result_id = %s;""",
            ('no',result_id)
           )
        
#push update
connection.commit()

#write culled results to CSV
cursor.execute("""
         SELECT result_id,docid,sentid,target_word,strat_phrase_root,strat_flag,strat_name_id,in_ref,source,phrase
        	FROM results 
        	WHERE (is_strat_name='yes' AND source='in_sent')
           OR (is_strat_name='yes' AND source='out_sent' AND in_ref='no')
     """)
     
results=cursor.fetchall()

with open('./output/results.csv', 'w') as outcsv:   
    #configure writer to write standard csv file
    writer = csv.writer(outcsv, delimiter=',', quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerow(['result_id','docid','sentid','target_word','strat_phrase_root','strat_flag','strat_name_id','in_ref','source','phrase'])
    for item in results:
        #Write item to outcsv
        writer.writerow([item[0], item[1], item[2],item[3], item[4], item[5],item[6], item[7], item[8], item[9]])

#close the postgres connection
connection.close()

