# Stromatolite Application Demonstration
We present a demonstration of the [GeoDeepDive](https://geodeepdive.org) text mining application used 
in Peters, Husson and Wilcots (in press, Geology). The goal of this application is to make tuples between
stromatolite fossils and stratigraphic names in order to assess the spatio-temporal distribution
of stromatolites across Earth history. This application uses a combination of Python and 
PostgreSQL, and is the same as used to generate the results for the published manuscript. We also 
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
git clone https://github.com/UW-Macrostrat/stromatolites_demo
cd stromatolites_demo
make
````
Note that it is likely that you may have to issue a sudo with the make command above.

Edit `credentials` with your username for your local Postgres database.

To create the database needed to run this demonstration, type:

````
make local_setup
````

To run the demonstration, type:

````
python run.py
````

Results are written to the `output` folder to the 
file `results.csv`. Please see `Results Summary` for a description of the fields returned.

NOTE: if `run.py` fails to run properly or does not produce results, one likely culprit is the `Python` dependencies did not install correctly, perhaps because of multiple installations of Python on your local machine. A way to fix this is to run:

````
python -m pip install <pkg>
````
for the offending packages. A good guess is that its failing to install the `stop-words` package, as the other Python dependencies are fairly common.


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
The `results` table is a CSV file exported to the folder `/output`. In the file, each row is a stratigraphic name 
that contains stromatolites according to the application logic - that is, each row is a "stromatolite-stratigraphic name" tuple.
Columns of each row contain information about the extracted tuple, including which document and phrase it came from and the link
between the discovered stratigraphic name and the Macrostrat database (if such a link exists). The columns are detailed below:

Column | Description 
-------|--------
result\_id| identifier for result tuple from the PostgreSQL results table
docid| identifier for the relevant document from the GeoDeepDive database, with metadata for it available through the GeoDeepDive API (i.e., [558dcf01e13823109f3edf8e](https://geodeepdive.org/api/articles?id=558dcf01e13823109f3edf8e))
sentid| identifier for sentence within the specified document where the tuple was extracted
target\_word| stromatolite word (i.e., stromatolite, stromatolites, stromatolitic).
strat\_phrase\_root| "unique" portion of the identified stratigraphic name inferred to contained stromatolites (i.e., "Wood Canyon" from the "Wood Canyon Formation")
strat\_flag| word that signified to the strat\_name extractor ([ext_strat_phrase.py](https://github.com/UW-Macrostrat/stromatolites/blob/master/udf/ext_strat_phrases.py)) that a word combination was a likely stratigraphic phrase (i.e., "Formation" for the "Wood Canyon Formation"). Note that this field could be "mention" for informal usage (i.e. "Wood Canyon stromatolites"), if a name has been formally defined in the same document.
strat\_name\_id| stratigraphic name id for the Macrostrat database. For example, [this api call](https://macrostrat.org/api/defs/strat_names?strat_name_id=2330) retrieves the definition for the "Wood Canyon Formation" from the Macrostrat database. [This api call](https://macrostrat.org/api/units?strat_name_id=2330) retrieves all lithostratigraphic units linked to the "Wood Canyon Formation" from the Macrostrat database. Note that this field could be "0" if the stratigraphic name describes a rock body outside of Macrostrat's areal coverage. If a name is linked to multiple stratigraphic names in the Macrostrat database, each identifier is separated by a "~" (i.e. "61671~446~2442").
in\_ref| application determination ([ext_references.py](https://github.com/UW-Macrostrat/stromatolites/blob/master/udf/ext_references.py)) if the extracted tuple came from the reference list of the specified document.
source| classifier indicating whether the extraction was from the same sentence ("in\_sent") or from a nearby sentence ("out\_sent").
phrase| full phrase that serves as basis for the determination that the stratigraphic phrase contains stromatolite fossils.

## License
CC-BY 4.0 International
