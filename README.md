# Running the DRYP Example with Overlapping Subdomains

## Prerequisites

Make sure MPI is available by loading the required module.

## Steps

1. Navigate to the DRYP package directory:

```bash
cd /shared/home1/c.c23086054/CUWALID-tutorials/Examples/DRYP
```


2. Load the MPI environment:

```bash
module load gompi/2025a
```

3. Run the DRYP model using MPI with 9 processes:

```bash
mpirun -np 9 python pardryp_sz/run_dryp_model_on_linux.py
```