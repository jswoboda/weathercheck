#!/bin/bash
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate base # change to your conda environment's name
# -u: unbuffered output
python /home/swoboj/weathercheck/bin/run_weather.py -r 120 -p 28800 -f /home/swoboj/weatherplots/ -d /home/swoboj/weatherdata