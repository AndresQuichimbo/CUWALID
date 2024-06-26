#!/bin/bash

# var definition
SYS=$(uname -s)
DIR=CUWALID
CWD=$(pwd)
ENV=cwld
ENJ=jptr
SPY=spdr
PYT=3.11.4
# the token below is gonna be removed in the future
TKN=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
MOD='lang/gcc/13.1.0'
mpath='/home/cuwalid/'


# CLONING REPOs
# -------------

mkdir $DIR

# jump into CUWALID
cd $DIR

# clone CUWALID training
stopar='CUWALID_training/stoPET/stopet_parameter_files/'
git clone https://$TKN@github.com/AndresQuichimbo/CUWALID_training.git

## download stoPET (& move it into training)
#ZIP=zome_file.zip
#STO=CUWALID_training/stoPET/stopet_parameter_files
#curl https://figshare.com/ndownloader/articles/19665531/versions/4 --output $ZIP
#mkdir $STO
#unzip $ZIP -d $STO
#rm zome_file.zip
#rm -r $STO/*.py

# alternative to not download stoPET-figsure
rsync -chavz $mpath$DIR/$stopar $stopar

# clone DRYP
git clone https://$TKN@github.com/AndresQuichimbo/DRYPv2.0.1.git
mv DRYPv2.0.1 DRYP

# clone STORM
git clone https://$TKN@github.com/feliperiosg/STORM3.git

cd $CWD


# EMPTY FOLDERS
# -------------

tr_p0=(forecast historical)
tr_p1=(model outputs postpp)
tr_p2=(csv fig netcdf raster)
mfldr='training/forecast/regional/model/'

for p0 in "${tr_p0[@]}"; do
   for p1 in "${tr_p1[@]}"; do
       if [[ "$p1" = "postpp" ]]; then
           for p2 in "${tr_p2[@]}"; do
               mkdir -p "training/$p0/regional/$p1/$p2"
               #echo "last level" 
           done
       else
           mkdir -p "training/$p0/regional/$p1"
           #echo "void dirs"
       fi
   done
done

printf "copying model files:\n"
rsync -chavz --exclude 'HAD_IMERGba_input_MAM_forecast_*' $mpath$mfldr $mfldr
rsync -chavz $mpath$mfldr'HAD_IMERGba_input_MAM_forecast_0_2022.dmp' $mfldr


ls -lthr


printf "\nsuccess!?\n"
