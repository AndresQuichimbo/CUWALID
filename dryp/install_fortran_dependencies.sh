cd dryp/components
f2py -c DRYP_uz_sz_interaction.f90 -m lakesf90 
f2py -c TransLoss.f90 -m faccumf90
f2py -c DRYP_solver.f90 -m gaussf90