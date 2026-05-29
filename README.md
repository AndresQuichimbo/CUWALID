# Running the DRYP Example with Overlapping Subdomains

## Prerequisites

Make sure MPI is available by loading the required module.

## Steps

1. Navigate to the DRYP directory inside the CUWALID-tutorials package [CUWALID-tutorials GitHub Repository](https://github.com/AndresQuichimbo/CUWALID-tutorials/tree/main):

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