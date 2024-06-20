Installation
============

Installing with docker
----------------------


Docker setup
^^^^^^^^^^^^^
Linux and MacOS
""""""""""""""""
Assuming docker is installed locally and running you can build a container to run the model as follows:-

(From project root)

.. parsed-literal::
    cd docker
    ./bin/build.sh
    ./bin/start.sh

The container can be stopped using:-

.. parsed-literal::
    cd docker
    ./bin/stop.sh

To destroy and rebuild the container (this will purge all docker containers and networks locally so use with caution):-

.. parsed-literal::
    cd docker
    ./bin/destroy.sh
    ./bin/build.sh
    ./bin/start.sh

Bash prompt in the container

.. parsed-literal::
    docker exec -it dryp-model /bin/bash
    Run the model
    TBC

.. parsed-literal::
    Running tests
    Run all tests:

.. parsed-literal::
    cd docker
    docker-compose -f docker-compose.yml exec dryp2 sh -c "cd /srv/projects/dryp/ && bash run_all_test.sh"

For running an individual test (e.g. test_save_csv.py):

.. parsed-literal::
    cd docker
    docker-compose -f docker-compose.yml exec dryp sh -c "cd /srv/projects/dryp/ && python test_save_csv.py" 

Compiling requirements
After updated requirements.in you need to compile requirements.txt as follows:-

.. parsed-literal::
    cd docker
    ./bin/compile_requirements.sh

Notes for Windows users
""""""""""""""""""""""""
How you build and start the container differs depending on how your computer is set up.

If you have the Ubuntu Windows Subsystem for Linux (WSL) installed on your Windows machine then you can use the shell scripts described above. https://apps.microsoft.com/store/detail/ubuntu-22042-lts/9PN20MSR04DW

If you don't have the Ubuntu Windows Subsystem for Linux (WSL) installed then you can build the container as follows:-

.. parsed-literal::
    docker compose build

and start it like this:-

.. parsed-literal::
    docker compose up -d


Installing in linux
--------------------

DRYP requires Python 3.11.4 or later. Installing DRYP in Linux can use directly the FORTRAN compliler. In this case the following
lines can be used for installing all Python packages:

.. parsed-literal::
    pip install -r requirements/requirements.in

To install FORTRAN dependencies the following can be used:

.. parsed-literal::
    sh install_fortran_dependencies.sh

Finally, to test the model the following line can be run:

.. parsed-literal::
    sh run_all_tests.sh
