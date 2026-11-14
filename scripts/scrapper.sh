#!/bin/bash
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate base # change to your conda environment's name
python /home/swoboj/weathercheck/bin/run_scraper.py --config ~/scrape_config.yaml
