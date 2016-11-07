#==============================================================================
#CHECKING AGE AGREEMENT BETWEEN DISCOVERED AND MATCHED STRATIGRAPHIC PHRASE
#==============================================================================

# ACQUIRE RELEVANT MODULES and DATA
#==============================================================================

import time, random, psycopg2, urllib2, csv, yaml

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
    

#Connect to Postgres
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


#initalize the age_check table
cursor.execute("""
    DELETE FROM age_check;
""")
connection.commit()

#initialize the age_agree column in strat_phrases
cursor.execute(""" 
        UPDATE  strat_phrases 
        SET     age_agree = '-';
""")
connection.commit()


#strat_phrases data dump
cursor.execute("""
    SELECT  DISTINCT ON(strat_name_id, int_name) 
    
            strat_phrase_root,
            strat_flag,
            strat_name_id,
            int_name,
            int_id 
            
            FROM strat_phrases
            
            WHERE strat_name_id<>'0' 
            AND int_name<>'na'
            
""")
    

#convert list of tuples to list of lists
int_list=cursor.fetchall()
int_list = [list(elem) for elem in int_list]

#gather list of unique strat_name_ids
strat_name_ids = set([i[2] for i in int_list])

#define overlap buffer between unit_ages and interval_ages
age_buff=25

#initialize summary variables
huh=0
yay=0
nay=0
int_check=[]

#loop through all unique strat_name ids to check extracted age - unit link congruency
for idx, name in enumerate(strat_name_ids):
    
    #find all strat_name_list - interval tuples to be checked
    name_check = [j for j in int_list if j[2]==name]
    
    #split into individual strat_name_ids by user-defined deilimiter
    strat_name_id = name.split('~')
    
    #initiliaze variables for checking
    unit_ages=[]
    skip=0
    
    #loop through each individual strat_name_id
    for match in strat_name_id:
        #hit the api to find unit_matches through /units route
        unit_link = download_csv( 'https://macrostrat.org/api/units?format=csv&strat_name_id=' + match )
        
        #if matches found, define b_age and t_age for a given strat_name from the constituent units
        if unit_link['headers']:        
            unit_ages.append([max(float(x) for x in unit_link['b_age']), min(float(x) for x in unit_link['t_age'])])
        else:
            unit_ages.append('na')
            skip+=1
    
    #loop through each individual strat_name_list - interval tuple    
    for idx2,row in enumerate(name_check):
        
        #initiliaze variables for checking
        age_check=[]
        int_id=row[4]
        age_def=row[3]        
        int_age=[]

        #case if interval information is a known interval name (AND at least one strat_name_id has a match)    
        if int_id!=0 and len(strat_name_id)!=skip:
            int_def   = download_csv( 'https://macrostrat.org/api/defs/intervals?format=csv&int_id=' + str(int_id) )
            int_age =  [float(int_def['b_age'][0]), float(int_def['t_age'][0])]

        #case if interval information is a numeric age (AND at least one strat_name_id has a match)
        elif len(strat_name_id)!=skip:
            age_def=age_def.split(' ')      

            #if units are Gyr
            if age_def[1].lower() in 'ga':
                try:
                    age=float(age_def[0])*1000
                    int_age = [abs(age), abs(age)]
                        
                except ValueError:
                    age='na'
            
            #if units are Myr
            else:
                try:
                    age=float(age_def[0])
                    int_age = [abs(age), abs(age)]
                    
                except:
                    age='na'
        
        #compare each individual strat_name age range to the interval information
        for unit in unit_ages:
            
            #case if unit or interval information not recovered
            if unit=='na' or not int_age:
                age_check.append('NA')
                huh+=1
                
            #case if unit and interval ages do not cross
            elif unit[0]+age_buff<int_age[1]-age_buff or unit[1]-age_buff>int_age[0]+age_buff:
                age_check.append('no')
                nay+=1
                
            #case if they do
            else:
                age_check.append('yes')
                yay+=1
        
        #summarize the findings for all strat_name_ids
        name_check[idx2].extend(['~'.join(age_check)])
        
        
        
    #dump to a local variable    
    [int_check.append(j) for j in name_check]
    
#write to PSQL table
for idx,i in enumerate(int_check):
    strat_phrase_root, strat_flag, strat_name_id, int_name, int_id, age_agree = i
    
    cursor.execute(""" 
        INSERT INTO age_check(        strat_phrase_root, 
                                      strat_flag, 
                                      strat_name_id, 
                                      int_name, 
                                      int_id, 
                                      age_agree)
        VALUES (%s, %s, %s, %s, %s, %s);""",
        (strat_phrase_root, strat_flag, strat_name_id, int_name, int_id, age_agree)
    )       


#push insertions
connection.commit()

#some sort of magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE age_check;
""")
connection.commit()


#splice strat_name_id-age tuples into the strat_phrases table
cursor.execute(""" UPDATE strat_phrases

                        SET age_agree = age_check.age_agree                        
                        FROM age_check
                        WHERE strat_phrases.strat_name_id = age_check.strat_name_id
                        AND strat_phrases.int_name = age_check.int_name

""")
connection.commit()

#some sort of magic
connection.set_isolation_level(0)
cursor.execute("""  VACUUM ANALYZE strat_phrases;
""")
connection.commit()

#close the connection
connection.close()
 
    
    
#summary statistic    
success = 'SUMMARY OF AGE CHECKS: yays = %s; nays = %s; unknown = %s' %(yay, nay, huh)

#summary of performance time
elapsed_time = time.time() - start_time
print '\n ###########\n\n %s \n elapsed time: %d seconds\n\n ###########\n\n' %(success,elapsed_time)

    
    
    
    
    
