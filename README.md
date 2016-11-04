# Stromatolite Application Demonstration
A demonstration of the [GeoDeepDive](https://geodeepdive.org) text mining application used 
in Peters, Husson and Wilcots (2016). The goal of this application is to make tuples between
stromatolite fossils and stratigraphic names in order to assess the spatio-temporal distribution
of stromatolites across Earth history. This repository includes 5 USGS Technical Reports 
from the GeoDeepDive database - a subset of the 8,425 documents analyzed for the manuscript.
Running this application will write results to the `output` - a list of stratigraphic names,
with links to the [Macrostrat](https://macrostrat.org) database if any were found.

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

To run an example, run `python run.py`. Results are written to the `output` folder.

## File Summary

#### config
A YAML file that contains project settings.


#### credentials
A YAML file that contains local postgres credentials for testing and generating examples.


#### requirements.txt
List of Python dependencies to be installed by `pip`


#### run.py
Python script that runs the entire application, including any setup tasks and exporting of results to the folder `/output`.


## License
CC-BY 4.0 International
