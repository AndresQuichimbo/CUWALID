@ECHO OFF

REM Variable Definitions
SET DIR=CUWALID
SET CWD=%cd%
SET MIN=%UserProfile%\miniconda3
SET MIN_BIN=%MIN%\condabin
SET ENV=cwld
SET ENJ=jptr
SET SPY=spdr
SET PYT=3.11.4
REM The token below is going to be removed in the future
SET TKN=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

REM Function to check if Miniconda is installed
:check_miniconda
IF EXIST "%MIN_BIN%\conda.bat" (
    ECHO Miniconda is already installed.
) ELSE (
    ECHO Miniconda is not installed. Installing Miniconda...
    GOTO install_miniconda
)

REM Function to install Miniconda
:install_miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
start /wait "" Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /S /D=%MIN%
DEL Miniconda3-latest-Windows-x86_64.exe

REM Add conda to PATH
SET PATH=%PATH%;%MIN_BIN%
GOTO check_miniconda

REM Check and install Miniconda if necessary
CALL :check_miniconda

ECHO version downloaded:
CALL conda --version

REM Update conda
CALL conda update -y -n base -c conda-forge conda
ECHO version updated to:
CALL conda --version

REM Create Conda environments
CALL conda create -y -n %ENV%
CALL conda create -y -n %ENJ%
CALL conda create -y -n %SPY%

REM Move into cuwalid environment and install packages
CALL conda activate %ENV%
CALL conda install -y -c conda-forge python=%PYT% geopandas rioxarray dask landlab pointpats scikit-image pip-tools chardet tqdm cartopy metpy numba cmaps cmcrameri seaborn nb_conda_kernels spyder-kernels ipykernel basemap bottleneck
CALL conda deactivate

REM Move into jupyter environment and install packages
CALL conda activate %ENJ%
CALL conda install -y -c conda-forge python=%PYT% jupyterlab nb_conda_kernels
CALL conda deactivate

REM Move into spyder environment and install packages
CALL conda activate %SPY%
CALL conda install -y -c conda-forge python spyder spyder-kernels ipython
CALL conda deactivate

CALL conda env list

REM CLONING REPOs
REM -------------
mkdir %DIR%

REM Jump into CUWALID
cd %DIR%

REM Clone CUWALID training
curl -LJO https://%TKN%@github.com/AndresQuichimbo/CUWALID_training/archive/refs/heads/main.zip
tar -xzf CUWALID_training-main.zip
RENAME CUWALID_training-main CUWALID_training
DEL /Q /S CUWALID_training-main.zip

REM Clone DRYP
curl -LJO https://%TKN%@github.com/AndresQuichimbo/DRYPv2.0.1/archive/refs/heads/main.zip
tar -xzf DRYPv2.0.1-main.zip
RENAME DRYPv2.0.1-main DRYP
DEL /Q /S DRYPv2.0.1-main.zip

REM Clone STORM
curl -LJO https://%TKN%@github.com/feliperiosg/STORM3/archive/refs/heads/main.zip
tar -xzf STORM3-main.zip
RENAME STORM3-main STORM3
DEL /Q /S STORM3-main.zip

cd /D %CWD%

dir %DIR%

ECHO:
ECHO success!?