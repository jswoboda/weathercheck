#!/bin/bash
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate base # change to your conda environment's name
# -u: unbuffered output
python /home/swoboj/weathercheck/bin/run_schedule.py -r 600 -p "00:00" -f /home/swoboj/weatherplots/ -d /home/swoboj/weatherdata -y /home/swoboj/keys/weatherconfig.yaml
