#==============================================================================
#GENERATE RESULTS TABLE
#==============================================================================

#path: /Users/jhusson/local/bin/deepdive-0.7.1/deepdive-apps/stromatolites/udf

#==============================================================================

import psycopg2, yaml

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

#initalize the results table
cursor.execute("""
    DELETE FROM results;
""")

#push drop/create to the database
connection.commit()

#gather results from the same-sentence inferences
cursor.execute(""" 
    INSERT INTO results (target_id, target_word, strat_phrase_root,strat_name_id, age_sum) 

		(SELECT target_id, target_word, strat_phrase_root,strat_name_id, age_sum
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
    INSERT INTO results (target_id, target_word, strat_phrase_root,strat_name_id, age_sum) 

		(SELECT target_id, target_word, strat_phrase_root,strat_name_id, age_sum
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

#push update
connection.commit()

# Disconnect from Postgres
connection.close()