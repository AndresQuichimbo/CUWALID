# DRYPv2.0
The development of DRYPv2.0 is part of the CUWALID modelling system.
It contains files required for the hydrological component (DRYP) of the CUWALID modelling system.

DRYPv2.0 is an optimized version for running large scale models.

This repository contains scripts for testing each of the main components of the model.

A detailed explanation of the model settings and simulation is presented in User_Guide.pdf


## Docker setup

### Linux and MacOS

Assuming docker is installed locally and running you can build a container to run the model as follows:-

(From project root)
```shell
cd docker
./bin/build.sh
./bin/start.sh
```

The container can be stopped using:-

```shell
cd docker
./bin/stop.sh
```

To destroy and rebuild the container (this will purge all docker containers and networks locally so use with caution):-

```shell
cd docker
./bin/destroy.sh
./bin/build.sh
./bin/start.sh
```

Bash prompt in the container
```shell
docker exec -it dryp-model /bin/bash
```

### Run the model
TBC


### Running tests
Run all tests:

```shell
cd docker
docker-compose -f docker-compose.yml exec dryp2 sh -c "cd /srv/projects/dryp/ && bash run_all_test.sh"
```

For running an individual test (e.g. test_save_csv.py):

```shell
cd docker
docker-compose -f docker-compose.yml exec dryp sh -c "cd /srv/projects/dryp/ && python test_save_csv.py" 
```


### Compiling requirements
After updated `requirements.in` you need to compile requirements.txt as follows:-

```shell
cd docker
./bin/compile_requirements.sh
```

### Notes for Windows users

How you build and start the container differs depending on how your computer is set up.

If you have the Ubuntu Windows Subsystem for Linux (WSL) installed on your Windows machine then you can use the shell 
scripts described above.
https://apps.microsoft.com/store/detail/ubuntu-22042-lts/9PN20MSR04DW

If you don't have the Ubuntu Windows Subsystem for Linux (WSL) installed then you can build the container as follows:-
```shell
docker compose build
```

and start it like this:-
```shell
docker compose up -d
```
