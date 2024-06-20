#!/bin/bash
# Must not be run from this directory, run from project root
docker-compose -f docker-compose.yml exec dryp2 sh -c "cd /srv/projects/dryp/requirements && pip-compile --allow-unsafe --generate-hashes --resolver=backtracking --output-file=requirements.txt requirements.in"
