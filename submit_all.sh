#!/bin/bash
set -e

# Navigate to the directory with .bash files
pushd bSub_runMe

# Read Storm JSON files and submit jobs for each
while IFS= read -r storm_json; do
    # Submit Storm job
    storm_jobid=$(qsub -v STORM_JSON="$storm_json" cuwalid_run_storm.bash | awk '{print $3}')
    
    # Submit StoPET job for the same JSON (without holding Storm job)
    stopet_json=$(echo "$storm_json" | sed 's/storm/stopet/')  # Assuming stopet json has the same name as storm json, just changed "storm" -> "stopet"
    stopet_jobid=$(qsub -v STOPET_JSON="$stopet_json" cuwalid_run_stopet.bash | awk '{print $3}')
    
    # Now submit DRYP jobs after Storm and StoPET (they should hold until both jobs are done)
    while IFS= read -r dryp_json; do
        # Create a DRYP job script for each DRYP JSON
        job_name=$(basename "$dryp_json" .json)
        bash_script="bSub_runMe/dryp_${job_name}.bash"

        cat <<EOF > "$bash_script"
#!/bin/bash
#$ -N dryp_${job_name}
#$ -l h_rt=01:00:00
#$ -l h_vmem=4G
#$ -pe smp 1
#$ -cwd
#$ -j y
#$ -V
#$ -S /bin/bash

source ~/miniconda3/bin/activate
conda activate cwld

# Run DRYP model with the provided JSON path
python -m cuwalid.dryp "$dryp_json" > bSub_logMe/dryp_${job_name}.log 2>&1
EOF

        chmod +x "$bash_script"

        # Submit the DRYP job, which depends on both Storm and StoPET jobs
        qsub -hold_jid $storm_jobid,$stopet_jobid "$bash_script"
    done < path/to/dryp_jsons.txt  # Path to your dryp_jsons.txt
done < path/to/storm_jsons.txt  # Path to your storm_jsons.txt

popd
