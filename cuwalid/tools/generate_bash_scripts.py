import os

def write_bash(job_name, command, logname=None):
    path = f"bSub_runMe/cuwalid_run_{job_name}.bash"
    log_file = logname or f"{job_name}.log"
    lines = [
        "#!/bin/bash\n",
        f"#$ -N cuwalid_{job_name}\n",
        "#$ -l h_rt=01:00:00\n",
        "#$ -l h_vmem=4G\n",
        "#$ -pe smp 1\n",
        "#$ -cwd\n",
        "#$ -j y\n",
        "#$ -V\n",
        "#$ -S /bin/bash\n",
        "\n",
        "source ~/miniconda3/bin/activate\n",
        "conda activate cwld\n",
        f"{command} > ../bSub_logMe/{log_file} 2>&1\n"
    ]
    with open(path, "w") as f:
        f.writelines(lines)

def main():
    os.makedirs("bSub_runMe", exist_ok=True)
    os.makedirs("bSub_logMe", exist_ok=True)

    # Only run STORM and StoPET jobs, since post-processing is now integrated
    write_bash("storm", "python -m cuwalid.storm.main_storm input_storm.json")
    write_bash("stopet", "python -m cuwalid.stopet.main_stopet_wrapper input_stopet.json")

    # Dryp jobs are generated separately later
    print("Run `submit_all.sh` after generating dryp_jsons.txt.")

if __name__ == "__main__":
    main()
