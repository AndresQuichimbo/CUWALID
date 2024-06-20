#!/bin/bash
# Must not be run from this directory, run from project root
docker-compose -f docker-compose.yml build --progress=plain --no-cache --build-arg USER_ID=`id -u` --build-arg GROUP_ID=`id -g`
docker-compose -f docker-compose.yml create
echo -e "\nNOW RUN ./bin/start\n"