@ECHO OFF

REM var definition
SET MIN=%UserProfile%\miniconda3\condabin\
SET ENV=cwld
SET ENJ=jptr
SET SPY=spdr
SET PYT=3.11.4

REM Function to check if Miniconda is installed
:check_miniconda
where conda >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    ECHO Miniconda is already installed.
) ELSE (
    ECHO Miniconda is not installed. Installing Miniconda...
    GOTO install_miniconda
)
GOTO setup_conda_envs

REM Function to install Miniconda
:install_miniconda
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda.exe
start /wait "" miniconda.exe /S /D=%UserProfile%\miniconda3
del miniconda.exe

REM add conda to PATH
SET PATH=%UserProfile%\miniconda3\Scripts;%UserProfile%\miniconda3;%PATH%
GOTO setup_conda_envs

REM Function to set up Conda environments
:setup_conda_envs
ECHO version downloaded:
call conda --version

REM update conda
call conda update -y -n base -c defaults conda
ECHO version updated to:
call conda --version

REM conda config --set auto_activate_base false

REM create the environments
call conda create -y -n %ENV%
call conda create -y -n %ENJ%
call conda create -y -n %SPY%

REM move into cuwalid
call conda activate %ENV%
call conda install -y -c conda-forge python=%PYT% geopandas rioxarray dask landlab pointpats scikit-image pip-tools chardet tqdm cartopy metpy numba cmaps cmcrameri seaborn nb_conda_kernels spyder-kernels ipykernel basemap bottleneck
call conda deactivate

REM move into jupyter
call conda activate %ENJ%
call conda install -y -c conda-forge python=%PYT% jupyterlab nb_conda_kernels
call conda deactivate

REM move into spyder
call conda activate %SPY%
call conda install -y -c conda-forge python spyder spyder-kernels ipython
REM call conda list
call conda deactivate

call conda env list

ECHO:
ECHO success!?
