#==============================================================================
#STRATIGRTAPHIC NAME EXTRACTOR
# ENTITIES = CAPITALIZED WORDS PRECEDING A STRATIGRAPHIC FLAG
# MENTIONS = DEFINED ENTITIES MINUS THE STRATIGRAPHIC FLAG
#
# ENTITY MAPPING DONE ON THE FULL SENTENCES TABLE
# MENTIONS DEFINED BY ENTITIES FOUND IN A GIVEN DOCUMENT
# MENTION MAPPIG DONE ON SENTENCES WITH A TARGET INSTANCE
#==============================================================================

# ACQUIRE RELEVANT MODULES
#==============================================================================
import time, urllib2, csv, random, psycopg2, re, string, yaml
from stop_words import get_stop_words
from psycopg2.extensions import AsIs

#tic
start_time = time.time()

#==============================================================================
# DEFINE FUNCTION TO DOWNLOAD CSV
#==============================================================================
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

#initalize the strat_phrases table
cursor.execute("""
    DELETE FROM strat_phrases;
""")

#IMPORT THE SENTENCES DUMP
cursor.execute("""
    SELECT docid, sentid, words FROM %(my_app)s_sentences_%(my_product)s;
""", {
    "my_app": AsIs(config['app_name']),
    "my_product": AsIs(config['product'].lower())
})
#sentences=cursor.fetchall()

#convert list of tuples to list of lists
#sentences = [list(elem) for elem in sentences]

#push drop/create to the database
connection.commit()

#==============================================================================
# DEFINE STRATIGRPAHIC VARIABLES
#==============================================================================

#get strat_names from Macrostrat API
strat_dict = download_csv( 'https://macrostrat.org/api/defs/strat_names?all&format=csv' )

#get interval_names from Macrostrat API
int_dict   = download_csv( 'https://macrostrat.org/api/defs/intervals?all&format=csv' )

#stop words
stop_words = get_stop_words('english')
stop_words = [i.encode('ascii','ignore') for i in stop_words]
alpha = list(string.ascii_lowercase);
alpha_period = [i+'.' for i in alpha]
stop_words = stop_words + ['lower','upper','research'] + alpha + alpha_period

#STRATIGRAPHIC VARIABLE DEFINITIONS
with open('./var/strat_variables.txt') as fid:
    strat_variables = fid.readlines()

for i in strat_variables:
    exec i

#==============================================================================
# LOOK FOR STRATIGRAPHIC NOMENCLATURE  - ENTITY RECOGNITION
#==============================================================================

#PRE-PROCESS: hack to replace weird strings
changed_docs=[];

#initialize the list of found names and list of documents
strat_list=[]
doc_list={}
to_write = []

#loop through sentences
for idx,line in enumerate(cursor):
    line = list(line)
    for ws in weird_strings:
        if ws[0] in ' '.join(line[2]):
            changed_docs.append([line[0], line[1], ws[0], ws[1]])
            line[2]=[word.replace(ws[0],ws[1]) for word in line[2]]
    line = tuple(line)

    #collect individual elements from the psql sentences dump
    doc_id, sent_id, words = line

    #initialize the variables needed to analyze words in sentence
    i = 0
    complete_phrase = []

    for word in words:
        i += 1

        #initial assumption is a found strat name will have no age information and no link to Macrostrat
        int_name="na"
        int_id='0'
        strat_name_id = '0'

        #initialize the lists of word indices and stratigraphic phrase words
        indices=[]
        strat_phrase = []

        #logic triggered by discovery of 'stratigraphic' flag (i.e. Formation, etc.)
        if word in strat_flags:
            #record the found word and its index
            indices.append(i)
            this_word = words[i-1]

            #initialize variables needed for analysis of preceding words
            preceding_words=[]
            j = 2

            #loop to identify preceding stratigraphic modifiers on GOOD_WORD (e.g. Wonoka Formation)
            #loop continues if:
            #   1) the beginning of sentence is not reached
            #   2) the preceding string is not empty
            #   3) the preceding word is not the current word
            #   4) the preceding word is capitalized
            #   5) the preceding capitalized word is not a stratigraphic flag (e.g. Member Wonoka Formation)
            #   6) the preceding word is not a capitalized stop word
            #   7) the preceding word does not contain a number
            while (i-j)>(-1) and len(words[i-j])!=0 and words[i-j] != words[i-j+1] and words[i-j][0].isupper() and words[i-j] not in strat_flags and words[i-j].lower() not in stop_words and re.findall(r'\d+',  words[i-j])==[]:
                #loop also broken if preceding word is an interval name (e.g. Ediacaran Wonoka Formation)
                if words[i-j] in int_dict['name']:
                    #record this interval name
                    int_name=words[i-j]

                    #list comprehensions to record interval id
                    locations = [k for k, t in enumerate(int_dict['name']) if t==int_name]
                    int_id = [int_dict['int_id'][I] for I in locations]
                    int_id=int_id[0]
                    break

                #loop also broken if preceding word is an age flag (i.e. 580 Ma. Wonoka Formation)
                elif words[i-j] in age_flags:
                    #record age flag with its preceding word (most likely a number)
                    int_name = words[i-j-1] + ' ' + words[i-j]
                    break

                #record qualifying preceding words and their indices
                preceding_words.append(words[i-j])
                indices.append((i-j))
                j += 1

            #if qualifying preceding words found, join them to the stratigraphic flag and create a stratigraphic phrase
            if preceding_words and len(preceding_words)<4:
                #create a full and partial stratigraphic phrase (i.e. with and without the stratigraphic flag)
                preceding_words.reverse()
                strat_phrase = ' '.join(preceding_words) + ' ' + this_word
                strat_phrase_cut = ' '.join(preceding_words)
                strat_flag=this_word

                #define term to check against Macrostrat's definitions
                # i.e.  Bitter Springs for Bitter Springs Formation
                #      Manlius Limestone for Manlius Limestone
                if strat_flag in lith_flags:
                    strat_phrase_check = strat_phrase
                else:
                    strat_phrase_check = strat_phrase_cut

                #index stratigraphic name to Macrostrat (if present)
                if strat_phrase_check in strat_dict['strat_name']:
                    #list comprehensions to record strat name id (all string matches regardless of inferred rank)
                    locations = [k for k, t in enumerate(strat_dict['strat_name']) if t==strat_phrase_check]
                    loc_ids = [strat_dict['strat_name_id'][L] for L in locations]
                    if loc_ids:
                        strat_name_id = '~'.join(str(e) for e in loc_ids)

                #beginning and end of stratigraphic phrase
                max_word_id = max(indices)
                min_word_id = min(indices)

                #create list of stratigraphic phrases found in a given sentence
                complete_phrase.append((idx, strat_phrase, strat_phrase_cut,strat_flag, doc_id, sent_id, max_word_id, min_word_id, strat_name_id,int_name,int_id, ' '.join(words)))

    #once sentence has been mined, add finds to growing list of stratigraphic names
    for idx,strat_phrase,strat_phrase_cut,strat_flag, doc_id, sent_id, max_word_id, min_word_id, strat_name_id,int_name,int_id, sentence in complete_phrase:

        #dump to local variable
        strat_list.append('\t'.join([str(x) for x in [idx, doc_id, sent_id, strat_phrase,strat_phrase_cut, strat_flag, min_word_id, max_word_id, strat_name_id,int_name,int_id, sentence]]))

        #make dictionary of (strat name, strat_name_id), separated by user defined delimiet, per doc id
        if doc_id in doc_list.keys():
            doc_list[doc_id].add(strat_phrase+DICT_DELIM+strat_name_id)
        else:
            doc_list[doc_id]=set([strat_phrase+DICT_DELIM+strat_name_id])

        to_write.append((doc_id, sent_id, strat_phrase,strat_phrase_cut, strat_flag, min_word_id, max_word_id, strat_name_id,int_name,int_id, sentence))

#write to PSQL table
cursor.executemany("""
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
                                  sentence)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""", to_write)


#push insertions
connection.commit()

#some sort of magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE strat_phrases;
""")
connection.commit()

#initalize the strat_dict table
cursor.execute("""
    DELETE FROM strat_dict;
""")

#write stratigraphic names found in documents to a PSQL table
for idx1,doc in enumerate(doc_list.keys()):
    strat_doc = list(doc_list[doc])
    cursor.execute("""
            INSERT INTO strat_dict(    docid,
                                       strat_phrase)
            VALUES (%s, %s);""",
            (doc, strat_doc)
        )

connection.commit()

#some sort of magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE strat_dict;
""")
connection.commit()

#close the postgres connection
connection.close()

#summary statistic
success = 'number of stratigraphic entities : %s' %len(strat_list)

#summary of performance time
elapsed_time = time.time() - start_time
print '\n ###########\n\n %s \n elapsed time: %d seconds\n\n ###########\n\n' %(success,elapsed_time)

#print out random result
r=random.randint(0,len(strat_list)-1); show = "\n".join(str(x) for x in strat_list[r].split('\t')); print "=========================\n" + show + "\n========================="


#%% OLD CODE
##IMPORT SENTENCES TO MINE
#fid = open('/Users/jhusson/local/bin/deepdive-0.7.1/app/stromatolites/tutorial/input/strat_locations.tsv','r')
#test = fid.readlines()
#fid.close()

##SPLIT LINE INTO TAB SEPARATED COMPONENTS
#elem = line.split('\t')

##WRITE DATA TO A FILE
#fid = open('/Users/jhusson/local/bin/deepdive-0.7.1/app/stromatolites/tutorial/input/strat_phrases.tsv','w')
#for item in strat_list:
#  fid.write("%s\n" % item)
#fid.close()

##USEFUL BIT OF CODE FOR LOOKING AT RANDOM SENTENCES
#r=random.randint(0,len(strat_locations)); elem=strat_locations[r].split('\t'); elem[4].replace("~^~"," ")

##USEFUL BIT OF CODE FOR LOOKING AT RANDOM RESULTS
#r=random.randint(0,len(strat_list)-1); show = "\n".join(str(x) for x in strat_list[r].split('\t')); show=show.replace(ARR_DELIM,' '); print "=========================\n" + show + "\n========================="


##USEFUL BIT OF CODE FOR LOOKING AT ALL RESULTS
#for item in strat_list:
#    show = "\n".join(str(x) for x in item.split('\t'))
#    print "=========================\n" + show + "\n========================="
#
#cursor.execute(""" SELECT * from sentences where doc_id='54b43272e138239d8685117b' and sent_id=352 """)
#dump=cursor.fetchall()
#
#cursor.execute(""" SELECT * from sentences where doc_id='54b43289e138239d868552b2' and sent_id=421 """)
#dump=cursor.fetchall()





