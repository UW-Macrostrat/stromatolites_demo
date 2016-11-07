#==============================================================================
#BUILD A BASIC BIBLIOGRAPHY
#==============================================================================

import json,psycopg2, yaml

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

#initialize the table
cursor.execute("""
    DELETE FROM bib
    """)

connection.commit()

#load in the bibJSON file
with open('./input/bibjson') as fid:
    bib=json.load(fid)

#push docid, authors, title, journal name and url to PostGRES
for idx,item in enumerate(bib):

    #initialize the variables to push to psql
    docid=[]
    title=[]
    journal=[]
    names=[]
    url =[]

    #as failsafe, always check if each variable exists
    if isinstance(item['_gddid'],unicode):
        docid=item['_gddid'].encode('ascii','ignore')
    else:
        docid=item['_gddid']

    if isinstance(item['title'],unicode):
        title=item['title'].encode('ascii','ignore')
    else:
        title=item['title']

    if isinstance(item['journal']['name'],unicode):
        journal=item['journal']['name'].encode('ascii','ignore')
    else:
        journal=item['journal']['name']

    if 'author' in item.keys():
        for name in item['author']:
            names.append(name['name'].encode('ascii','ignore'))

    if 'link' in item.keys():
        url=item['link'][0]['url']

        for link in item['link']:
            if link['type']=='sciencedirect':
                url=link['url']


    #psql table insertion
    cursor.execute("""
            INSERT INTO bib (         docid,
                                      author,
                                      title,
                                      journal,
                                      url)
            VALUES (%s, %s, %s, %s, %s);""",
            (docid,names,title,journal,url)
    )

connection.commit()

#update the table with number of instances per journal name
cursor.execute("""  WITH  query AS(SELECT journal, COUNT(journal)
                                  FROM bib
                                  GROUP BY journal)

                    UPDATE bib
                        SET journal_instances = query.count
                        FROM query
                        WHERE bib.journal = query.journal

""")
connection.commit()

#close the connection
connection.close()

