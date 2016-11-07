#==============================================================================
#INITIALIZE POSTGRES TABLES
#==============================================================================


import yaml
import psycopg2
from psycopg2.extensions import AsIs

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

#SENTENCES TABLE
#DROP TABLE IF EXISTS sentences CASCADE;
#CREATE TABLE sentences (docid text, sentid integer, wordidx integer[], words text[], poses text[], ners text[], lemmas text[], dep_paths text[], dep_parents integer[]);
#COPY sentences FROM '/Users/jhusson/local/bin/deepdive-0.7.1/deepdive-apps/stromatolites/input/strom_nlp352';


#TARGET_INSTANCES    
cursor.execute("""
    DROP TABLE IF EXISTS target_instances CASCADE;
    CREATE TABLE target_instances(
        target_id serial PRIMARY KEY,
        docid text,
        sentid int,
        target_word text,
        num_strat_doc int DEFAULT 0,
        target_word_idx int[],
        target_pose text[],
        target_path text[],
        target_parent int[],
        target_children text,
        sentence text);
""")
connection.commit()

#TARGET_ADJECTIVES    
cursor.execute("""
    DROP TABLE IF EXISTS target_adjectives CASCADE;
    CREATE TABLE target_adjectives(
        docid text,
        sentid int,
        target_id int,
        target_word text,
        target_adjective text);
""")
connection.commit()

#STRAT_PHRASES
cursor.execute("""
    DROP TABLE IF EXISTS strat_phrases CASCADE;
    CREATE TABLE strat_phrases(
        docid text,
        sentid int,
        strat_phrase text,
        strat_phrase_root text,
        num_phrase int,
        sentence text,
        strat_flag text,
        phrase_start int,
        phrase_end int,
        strat_name_id text,
        int_name text,
        int_id int,
        age_agree text DEFAULT '-');
""")
connection.commit()

#STRAT_DICT
cursor.execute("""
    DROP TABLE IF EXISTS strat_dict CASCADE;
    CREATE TABLE strat_dict(
        docid text,
        strat_phrase text[]);
""")
connection.commit()


#STRAT_TARGET
cursor.execute("""
    DROP TABLE IF EXISTS strat_target CASCADE;
    CREATE TABLE strat_target(
        docid text,
        sentid int,
        refs_loc int,
        in_ref text DEFAULT 'no',
        strat_phrase_root text,
        num_phrase int,
        target_relation text,
        target_distance int,
        sentence text,
        strat_flag text,
        strat_name_id text,
        strat_start int,
        strat_end int,
        int_name text,
        age_agree text DEFAULT '-',
        age_sum text DEFAULT '-',
        words_between text[],
        target_word text,
        target_word_idx int[],
        target_id int
        );
""")
connection.commit()

#AGE CHECK
cursor.execute("""
    DROP TABLE IF EXISTS age_check CASCADE;
    CREATE TABLE age_check(
        strat_phrase_root text,
        strat_flag text,
        strat_name_id text,
        int_name text,
        int_id int,
        age_agree text);
""")
connection.commit()

#STRAT_TARGET_DISTANT
cursor.execute("""
    DROP TABLE IF EXISTS strat_target_distant CASCADE;
    CREATE TABLE strat_target_distant(
        docid text,
        sentid int,
        refs_loc int,
        in_ref text DEFAULT 'no',
        strat_phrase_root text,
        strat_flag text,
        num_phrase int,
        int_name text,
        strat_name_id text,
        age_agree text DEFAULT '-',
        age_sum text DEFAULT '-',
        words_between text,
        target_sent_dist int, 
        target_word text,
        target_parent text [],
        target_children text [],
        target_id int
        );
""")
connection.commit()


#BIB
cursor.execute("""
    DROP TABLE IF EXISTS bib CASCADE;
    CREATE TABLE bib(
        docid text,
        author text[],
        title text,
        journal text,
        url text,
        journal_instances int
        );
""")
connection.commit()

#RESULTS
cursor.execute("""
    DROP TABLE IF EXISTS results CASCADE;
    CREATE TABLE results(
        target_id int,
        docid text,
        sentid int,
        target_word text,
        strat_phrase_root text,
        strat_name_id  text,
        age_sum text,
        source text,
        phrase text
        );
""")
connection.commit()

# Disconnect from Postgres
connection.close()