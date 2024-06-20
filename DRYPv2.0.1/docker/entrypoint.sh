#!/bin/bash
set -e

# Compile libraries
cd /srv/projects/dryp/dryp/components/ && f2py -c DRYP_uz_sz_interaction.f90 -m lakesf90
cd /srv/projects/dryp/dryp/components/ && f2py -c TransLoss.f90 -m faccumf90
cd /srv/projects/dryp/dryp/components/ && f2py -c DRYP_solver.f90 -m gaussf90

# Stop container from exiting
tail -f /dev/null