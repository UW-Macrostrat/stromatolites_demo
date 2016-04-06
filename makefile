all:
	cp credentials.example credentials;
	pip install -r requirements.txt;



local_setup:
	./setup/setup.sh
