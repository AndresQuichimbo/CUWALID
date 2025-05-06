import sys
import json
import os
import numpy as np

from cuwalid.storm.pdfs_ import masking
from cuwalid.storm.rainfall import construct_pdfs, nc_bytes, read_pdfs, regionalisation, replicate_, run_single_simulation, wrapper
from cuwalid.storm.checks_ import welcome, assertion
from cuwalid.storm.parameters import *

ptot_or_kmean = 1  # 1 if seasonal.rain sampled; 0 if taken from shp.kmeans
capmax_or_not = 1  # 1 if using MAXD_RAIN as capping limit; 0 if using iMAX
output_stats_ = 0  # 1 if willing to produce CSV.file; 0 saves some ram.mem
tunnin = 7

def main(config_path, sim_index):
    with open(config_path, 'r') as f:
        config = json.load(f)

    sim_index = int(sim_index)

    # Extract config values
    NUMSIMS = config["NUMSIMS"]
    NUMSIMYRS = config["NUMSIMYRS"]
    SEASON_TAG = config["SEASON_TAG"]
    SEED_YEAR = config["SEED_YEAR"]
    OUT_PATH = config["OUT_PATH"]
    TER_FILE = config["TER_FILE"]
    PDF_FILE = config["PDF_FILE"]
    DEM_FILE = config["DEM_FILE"]
    SHP_FILE = config["SHP_FILE"]
    ZON_FILE = config["ZON_FILE"]

    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)

    # Set up simulation environment
    willkommen = welcome(NUMSIMS, NUMSIMYRS, SEED_YEAR, SEASON_TAG, OUT_PATH)
    assertion(willkommen.wet_hash, NUMSIMS, NUMSIMYRS, DEM_FILE, SHP_FILE)
    NC_NAMES = willkommen.ncs

    n_sim_y_indicator = replicate_(NUMSIMS, NUMSIMYRS)
    nc_bytes()


    upd_max = np.min((MAXD_RAIN, iMAX)) if capmax_or_not == 1 else iMAX
    maxima = np.array(((upd_max - ADD) / SCL) + MINIMUM, dtype=RAINFMT)

    PDFS = read_pdfs(PDF_FILE, SEASON_TAG)
    construct_pdfs(PDFS)

    SPACE = masking(SHP_FILE)
    region_s = regionalisation(ZON_FILE.replace('.shp', f'_{SEASON_TAG}_{NREGIONS}r.shp'), 'region', 'u_rain', SPACE)

    if TER_FILE:
        icpac_s = regionalisation(TER_FILE, 'region', 'tercile', SPACE, add=-2)
    else:
        icpac_s = {'npma': [region_s['npma'][0].copy()]}
        icpac_s['npma'][0][:] = 1

    print(f"Running STORM simulation {sim_index + 1} / {NUMSIMS * NUMSIMYRS}")
    run_single_simulation(
        sim_index,
        NC_NAMES[sim_index],
        NC_NAMES,
        SPACE,
        PDFS,
        SEED_YEAR,
        NUMSIMYRS,
        SEASON_TAG,
        TER_FILE,
        region_s,
        icpac_s,
        n_sim_y_indicator,
        maxima,
        upd_max,
        PTOT_SC,
        PTOT_SF,
        iMAX,
        ADD,
        SCL
    )
    print("Simulation complete.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_storm_simulation.py <storm_input.json> <sim_index>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
