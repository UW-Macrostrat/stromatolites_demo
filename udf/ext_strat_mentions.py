##==============================================================================
## LOOK FOR STRATIGRAPHIC NOMENCLATURE  - MENTION RECOGINITION
##==============================================================================

# ACQUIRE RELEVANT MODULES
#==============================================================================
import time, urllib2, csv, random, psycopg2, re, yaml
from psycopg2.extensions import AsIs

#tic
start_time = time.time()

#function for dowloading CSVs from a URL
def download_csv( url ):
    
    #return variable
    dump_dict = {}
    
    #get strat_names from Macrostrat API
    dump = urllib2.urlopen( url )
    dump = csv.reader(dump)
    
    #unpack downloaded CSV as list of tuples
    #--> length of VARIABLE == number of fields
    #--> length of VARIABLE[i] == number of rows
    #--> VARIABLE[i][0] = header name
    cols = list(zip(*dump))
    
    #key names correspond to field names (headers in the CSV file)
    for field in cols:
        dump_dict[field[0]]=field[1:]
        
    dump_dict['headers'] = sorted(dump_dict.keys())
    
    return dump_dict

#==============================================================================
# CONNECT TO POSTGRES
#==============================================================================

# Connect to Postgres
with open('./credentials', 'r') as credential_yaml:
    credentials = yaml.load(credential_yaml)

with open('./config', 'r') as config_yaml:
    config = yaml.load(config_yaml)
    
connection = psycopg2.connect(
    dbname=credentials['postgres']['database'],
    user=credentials['postgres']['user'],
    host=credentials['postgres']['host'],
    port=credentials['postgres']['port'])
cursor = connection.cursor()

#initialize mentions
cursor.execute("""DELETE FROM strat_phrases WHERE strat_flag='mention';
""")

#import sentences to mine - just restricted to sentences with target instance
cursor.execute("""
    SELECT  DISTINCT ON (target_instances.docid,
            target_instances.sentid)
            
            target_instances.docid,
            target_instances.sentid,
            %(my_app)s_sentences_%(my_product)s.words
   FROM     %(my_app)s_sentences_%(my_product)s, target_instances
   WHERE    %(my_app)s_sentences_%(my_product)s.docid = target_instances.docid
   AND      %(my_app)s_sentences_%(my_product)s.sentid = target_instances.sentid;
""",{
    "my_app": AsIs(config['app_name']),
    "my_product": AsIs(config['product'].lower())
})
sentences=cursor.fetchall()

#convert list of tuples to list of lists
sentences = [list(elem) for elem in sentences]

#import docid - strat_name tuples
cursor.execute("""
    SELECT  * FROM strat_dict;
""")
connection.commit()

strat_dict = cursor.fetchall()

#convert list of tuples to list of lists
strat_dict = [list(elem) for elem in strat_dict]

#make a dictionary of docid-strat_name tuples
doc_list={}
for i in strat_dict:
    doc_list[i[0]]=set(i[1])
    
#==============================================================================
# DEFINE STRATIGRPAHIC VARIABLES
#==============================================================================

#get interval_names from Macrostrat API
int_dict   = download_csv( 'https://macrostrat.org/api/defs/intervals?all&format=csv' )

#user-defined variables
with open('./var/strat_variables.txt') as fid:
    strat_variables = fid.readlines()
    
for i in strat_variables:
    exec i

#PRE-PROCESS: hack to replace weird strings
for idx,line in enumerate(sentences):
    for ws in weird_strings:
        if ws[0] in ' '.join(sentences[idx][2]):
            sentences[idx][2]=[word.replace(ws[0],ws[1]) for word in sentences[idx][2]] 


#with a dictionary of stratigraphic entites mapped to a given document, find the mentions
# i.e. find 'the Bitter Springs stromatolite' after identifying 'the Bitter Springs Formation'
strat_flag = 'mention'
age_agree='-'

strat_list=[]

#loop through documents with discoverd stratigraphic entities
for idx1,doc in enumerate(doc_list.keys()):
    #list of sentences data from a given document
    target_sents = [k for k in sentences if k[0]==doc]
    #list of stratigraphic names associated with that document
    target_strat = list(doc_list[doc])
    
    
    #loop through sentence data per document
    for idx2,line in enumerate(target_sents):
        doc_id, sent_id, words = line
                
        sentence = ' '.join(words)
    
        for name in target_strat:
            #parse the (strat_name, strat_name_id) tuple
            strat_phrase=name.split(DICT_DELIM)[0]
            strat_phrase=strat_phrase.split(' ')
            strat_phrase=' '.join(strat_phrase[0:-1])            
            
            strat_name_id=name.split(DICT_DELIM)[1]
            
            matches=[m.start() for m in re.finditer(r'\b' + strat_phrase + r'\b',sentence)]
            
            if matches:
                #if at least one match is found, count number of spaces backward to arrive at word index
                name_idx = [sentence[0:m].count(' ') for m in matches]
                #remove double hits (i.e. stromatolitic-thrombolitic)
                name_idx = list(set(name_idx))
                #split the strat mention into parts
                name_part = strat_phrase.split(' ')
           
                #loop through all discoveries                
                for i in name_idx:
                    #record it as a mention if:
                    #   1) it is not at the end of the sentence
                    #   2) the phrase is not followed by a strat_flag
                    #       (this is to avoid duplication)
                    #   3) the mention is not part of garbled table e.g. 'Tumbiana Tumbiana Tumbiana Tumbiana'
                    if i<len(words)-len(name_part) and words[i+len(name_part)] not in strat_flags and words[i] != words[i+1]:                    
                        int_name='na'
                        int_id='0'
                        
                        #look to see if there is an interval name before the mention
                        if i>1 and words[i-1] in int_dict['name']:
                            #record this interval name
                            int_name=words[i-1]
                            #list comprehensions to record interval id
                            locations = [k for k, t in enumerate(int_dict['name']) if t==int_name]
                            int_id = [int_dict['int_id'][I] for I in locations]
                            int_id=int_id[0]                        
                        
                        #look to see if there is an age_flag before the mention
                        elif i>1 and words[i-1] in age_flags:
                            #record age flag with its preceding word (most likely a number)
                            int_name = words[i-2] + ' ' + words[i-1]
                        
                        #record where mention is found
                        max_word_id = str(i+len(name_part))
                        min_word_id = str(i)
                        
                        #add to local variable
                        strat_list.append('\t'.join(str(x) for x in [idx2, doc_id, sent_id,name.split(DICT_DELIM)[0], strat_phrase,strat_flag, min_word_id, max_word_id, strat_name_id,int_name,int_id, sentence]))
                        
                        #write to PSQL table
                        cursor.execute(""" 
                            INSERT INTO strat_phrases(    docid,
                                                          sentid,
                                                          strat_phrase,
                                                          strat_phrase_root,
                                                          strat_flag,
                                                          phrase_start,
                                                          phrase_end,
                                                          strat_name_id,
                                                          int_name,
                                                          int_id,
                                                          sentence,
                                                          age_agree)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                            (doc_id, sent_id,name.split(DICT_DELIM)[0], strat_phrase, strat_flag, min_word_id, max_word_id, strat_name_id,int_name,int_id, sentence, age_agree)
                            )           

#push insertions to the database
connection.commit()

#some sort of magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE strat_phrases;
""")
connection.commit()

connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE target_instances;
""")
connection.commit()
     

#summarize the number of DISTINCT strat_name_roots found in a given sentence
cursor.execute("""  WITH  query AS(SELECT docid, sentid,
                                  COUNT(DISTINCT strat_phrase_root) AS count
                                  FROM strat_phrases
                                  GROUP BY docid,sentid)
                            
                    UPDATE strat_phrases
                        SET num_phrase = query.count
                        FROM query
                        WHERE strat_phrases.docid = query.docid
                        AND strat_phrases.sentid = query.sentid

""")
connection.commit()

#summarize the number of DISTINCT strat_name_roots found for a given document
cursor.execute("""  WITH  query AS(SELECT docid,
                                  COUNT(DISTINCT strat_phrase_root) AS count
                                  FROM strat_phrases
                                  GROUP BY docid)
                            
                    UPDATE target_instances
                        SET num_strat_doc = query.count
                        FROM query
                        WHERE target_instances.docid = query.docid
""")
connection.commit()      

#close the postgres connection
connection.close()

#summary statistic    
success = 'number of stratigraphic mentions : %s' %len(strat_list)

#summary of performance time
elapsed_time = time.time() - start_time
print '\n ###########\n\n %s \n elapsed time: %d seconds\n\n ###########\n\n' %(success,elapsed_time)

#print out random result
r=random.randint(0,len(strat_list)-1); show = "\n".join(str(x) for x in strat_list[r].split('\t')); print "=========================\n" + show + "\n========================="

