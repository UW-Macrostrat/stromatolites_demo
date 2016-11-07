#==============================================================================
#TARGET NAME EXTRACTOR
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

#initalize the target_instances table
cursor.execute("""
    DELETE FROM target_instances;
""")

#IMPORT THE SENTENCES DUMP
cursor.execute("""
    SELECT docid, sentid, words, poses, dep_paths, dep_parents FROM %(my_app)s_sentences_%(my_product)s;
""", {
    "my_app": AsIs(config['app_name']),
    "my_product": AsIs(config['product'].lower())
})

#push drop/create to the database
connection.commit()


#initalize list of target occurences
target_list=[]

#TARGET DEFINITIONS
with open('./var/target_variables.txt') as fid:
    target_variables = fid.readlines()

for i in target_variables:
    exec i

#loop through all sentences.
to_write = []
for line in cursor:
    #collect individual elements from the psql sentences dump
    docid, sentid, words, poses, dep_paths, dep_parents = line

    #initialize list of local target occurences
    targets = []

    #sentence string
    sent = ' '.join(words)

    #loop through all the target names
    for name in target_names:
	#starting index of all matches for a target_name in the joined sentence
	matches=[m.start() for m in re.finditer(name,sent.lower())]

	if matches:
	    #if at least one match is found, count number of spaces backward to arrive at word index
	    indices = [sent[0:m].count(' ') for m in matches]
	    #remove double hits (i.e. stromatolitic-thrombolitic)
	    indices = list(set(indices))
	    #target_name spans its starting word index to the number of words in the phrase
	    target_word_idx = [[i,i+len(name.split(' '))] for i in indices]

	    #initialize other data about a found target_name
	    target_pose=[]
	    target_path=[]
	    target_parent=[]

	    for span in target_word_idx:
		#poses, paths and parents can be found at same indices of a target_name find
		target_word = ' '.join(words[span[0]:span[1]])

		if target_word.lower() not in bad_words:
		    target_children=[]
		    target_pose = poses[span[0]:span[1]]
		    target_path = dep_paths[span[0]:span[1]]
		    target_parent = dep_parents[span[0]:span[1]]

		    #children of each component of a target_name
		    for span_idx in range(span[0], span[1]):
			children = [j for j,i in enumerate(dep_parents) if i==span_idx+1]
			target_children.append(children)

		    #convert parent_ids to Pythonic ids
		    target_parent = [i-1 for i in target_parent]

		    #add finds to a local variable
		    target_list.append([docid, sentid, target_word, span, target_pose, target_path, target_parent, target_children, sent])

		    #for easier storage, convert list of target_children lists to a string
		    str_target_children = str(target_children)

		    #write to PSQL table
                    to_write.append(
			(docid, sentid, target_word, span, target_pose, target_path, target_parent, str_target_children, sent)
			)

cursor.executemany("""
INSERT INTO target_instances(    docid,
				sentid,
				target_word,
				target_word_idx,
				target_pose,
				target_path,
				target_parent,
				target_children,
				sentence)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
to_write
)

#push insertions to the database
connection.commit()

#restart the primary key
cursor.execute("""
    ALTER TABLE target_instances DROP target_id;
""")

#push drop/create to the database
connection.commit()

#add primary key
cursor.execute(""" ALTER TABLE target_instances ADD COLUMN target_id SERIAL PRIMARY KEY;
""")
connection.commit()


#do some magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE target_instances;
""")
connection.commit()

#close the connection
connection.close()

#summary statistic
success = 'number of target instances: %s' %len(target_list)

#summary of performance time
elapsed_time = time.time() - start_time
print '\n ###########\n\n %s \n elapsed time: %d seconds\n\n ###########\n\n' %(success,elapsed_time)


#USEFUL BIT OF CODE FOR LOOKING AT RANDOM RESULTS
r=random.randint(0,len(target_list)-1); print "=========================\n"; print("\n".join(str(target) for target in target_list[r])); print  "\n========================="
