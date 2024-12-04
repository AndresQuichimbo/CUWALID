#!/bin/bash

# var definition
SYS=$(uname -s)
ENV=cwld
ENJ=jptr
SPY=spdr
PYT=3.11.4

# Function to check if Miniconda is installed
check_miniconda() {
    if command -v conda &> /dev/null; then
        echo "Miniconda is already installed."
    else
        echo "Miniconda is not installed. Installing Miniconda..."
        install_miniconda
    fi
}

# Function to install Miniconda
install_miniconda() {
    mkdir -p ~/miniconda3
    # Download Miniconda installer
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    # Run the Miniconda installer
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    # Initialize Miniconda
    ~/miniconda3/bin/conda init bash
    # Source conda
    . $HOME/miniconda3/etc/profile.d/conda.sh
    # Deactivate base (only once)
    conda config --set auto_activate_base false
    # Update conda
    conda update -y -n base -c defaults conda
}

# Check and install Miniconda if necessary
check_miniconda

# Create Conda environments
conda create -y -n $ENV
conda create -y -n $ENJ
conda create -y -n $SPY

# Move into cuwalid environment and install packages
conda activate $ENV
conda install -y -c conda-forge python=$PYT geopandas rioxarray dask landlab pointpats scikit-image pip-tools chardet tqdm cartopy metpy numba cmaps cmcrameri nb_conda_kernels seaborn spyder-kernels ipykernel basemap bottleneck osmnx geopy matplotlib-scalebar
conda deactivate

# Move into jupyter environment and install packages
conda activate $ENJ
conda install -y -c conda-forge python=$PYT jupyterlab nb_conda_kernels
conda deactivate

# Uncomment if you want to set up the spyder environment
# Move into spyder environment and install packages
#conda activate $SPY
#conda install -y -c conda-forge python spyder spyder-kernels ipython
#conda deactivate

# List Conda environments
echo "Conda environments created:
conda env list