# Stromatolite Application Demonstration
A demonstration of the [GeoDeepDive](https://geodeepdive.org) text mining application used 
in Peters, Husson and Wilcots (2016). The goal of this application is to make tuples between
stromatolite fossils and stratigraphic names in order to assess the spatio-temporal distribution
of stromatolites across Earth history. This application uses a combination of Python and 
PostgreSQL, and is the same as used to generate the results for the manuscript. We also 
include 5 USGS Technical Reports from the GeoDeepDive database - a subset of the 8,425 
documents analyzed for the manuscript - to serve as a demonstration of how the application
operates.

## Getting started
Dependencies:
  + [GNU Make](https://www.gnu.org/software/make/)
  + [git](https://git-scm.com/)
  + [pip](https://pypi.python.org/pypi/pip)
  + [PostgreSQL](http://www.postgresql.org/)

### OS X
OS X ships with GNU Make, `git`, and Python, but you will need to install `pip` and PostgreSQL.

To install `pip`:
````
sudo easy_install pip
````

To install PostgreSQL, it is recommended that you use [Postgres.app](http://postgresapp.com/). Download
the most recent version, and be sure to follow [the instructions](http://postgresapp.com/documentation/cli-tools.html)
for setting up the command line tools, primarily adding the following line to your `~/.bash_profile`:

````
export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/latest/bin
````


### Setting up the project
First, clone this repository and run the setup script:

````
git clone https://github.com/UW-Macrostrat/stromatolites
cd stromatolites
make
````

Edit `credentials` with your username for your local Postgres database.

To create a database with the data included in `/setup/usgs_example`:

````
make local_setup
````

To run an example, run `python run.py`. Results are written to the `output` folder to the 
file `results.csv`. Please see `Results Summary` for a description of the fields returned.

## File Summary

#### config
A YAML file that contains project settings.


#### credentials
A YAML file that contains local postgres credentials for testing and generating examples.


#### requirements.txt
List of Python dependencies to be installed by `pip`


#### run.py
Python script that runs the entire application, including any setup tasks and exporting of results to the folder `/output`.

## Results Summary
Column | Description 
-------|--------
result\_id| identifier for "stromatolite-stratigraphic name" result tuple from the results table
docid| identifier for document with the GeoDeepDive database (i.e., [558dcf01e13823109f3edf8e](https://geodeepdive.org/api/articles?id=558dcf01e13823109f3edf8e))
sentid| identifier for sentence within the document where the tuple was extracted
target\_word| "stromatolite" word
strat\_phrase\_root| unique portion of the identified stratigraphic name inferred to contained stromatolites (i.e., "Wood Canyon" fron the "Wood Canyon Formation")
strat\_flag| word that signified to the `strat\_name` extractor that a phrase was a stratigraphic phrase (i.e., "Formation"). Note that this field could be "mention" for informal usage once a name has been formally defined in the same document (i.e. "Wood Canyon stromatolites").
strat\_name\_id| identifier for the extracted name linked to the Macrostrat database. For example, [this api call](https://macrostrat.org/api/defs/strat_names?strat_name_id=2330) retrieves the definition for the "Wood Canyon Formation" from the Macrostrat database. [This api call](https://macrostrat.org/api/units?strat_name_id=2330) retrieves all lithostratigraphic units linked to the "Wood Canyon Formation" from the Macrostrat database. Note that this field could be "0" if no link to Macrostrat is discovered. If a name is linked to multiple stratigraphic names in the Macrostrat database, each identifier is separated by a ~ (i.e. "61671~446~2442").
in\_ref| application determination if the extracted tuple came from the reference list.
source| classifier indicating whether the extraction was from the same sentence ("in\_sent") and from a nearby sentence ("out\_sent").
phrase| full phrase that discusses the stratigraphic phrase and stromatolite fossil(s).

## License
CC-BY 4.0 International
