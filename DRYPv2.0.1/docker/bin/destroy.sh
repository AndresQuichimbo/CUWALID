#!/bin/bash
# Must not be run from this directory, run from project root
docker stop $(docker ps -a -q)
docker network prune --force
echo -e "\nBRINGING DOWN CONTAINERS AND DELETING VOLUMES\n"
docker-compose -f docker-compose.yml down --volumes --remove-orphans
