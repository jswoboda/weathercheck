#!python

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
import pandas as pd
import schedule
import yaml

from weathercheck import get_bme280_data, mkdf, send_email, sys_stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ipdb


def parse_command_line(str_input=None):
    """This will parse through the command line arguments

    Function to go through the command line and if given a list of strings all
    also output a namespace object.

    Parameters
    ----------
    str_input : list
        A list of strings or the input from the command line.

    Returns
    -------
    input_args : Namespace
        An object holding the input arguments wrt the variables.
    """
    scriptpath = Path(sys.argv[0])
    scriptname = scriptpath.name

    formatter = argparse.RawDescriptionHelpFormatter(scriptname)
    width = formatter._width
    title = "Run Weather Recording"
    shortdesc = "Plots and runs the weather recording."
    desc = "\n".join(
        (
            "*" * width,
            "*{0:^{1}}*".format(title, width - 2),
            "*{0:^{1}}*".format("", width - 2),
            "*{0:^{1}}*".format(shortdesc, width - 2),
            "*" * width,
        )
    )
    # desc = "This is the run script for SimVSR."
    # if str_input is None:
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # else:
    #     parser = argparse.ArgumentParser(str_input)
    parser.add_argument(
        "-t",
        "--thresh",
        dest="thresh_f",
        help="Temperature threshold threshold to send email.",
        default=55.0,
        type=float,
    )
    parser.add_argument(
        "-r",
        "--revisit_time",
        dest="revisit_time",
        help="Number of seconds to revisit the measurmeent.",
        required=True,
        type=int,
    )
    parser.add_argument(
        "-p",
        "--plottod",
        dest="plottod",
        help="The time of day the plotting will be made.",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-f",
        "--plotdir",
        dest="plotdir",
        help="Directory where plots will be saved.",
        default="/home/swoboj/weatherplots",
    )
    parser.add_argument(
        "-d",
        "--datadir",
        dest="datadir",
        help="Directory where the data will be saved",
        default="/home/swoboj/weatherdata",
    )
    parser.add_argument(
        "-y",
        "--yamlconfig",
        dest="yamlconfig",
        help="The configuration file for the email.",
        required=True,
        type=str,
    )

    if str_input is None:
        return parser.parse_args()
    return parser.parse_args(str_input)


# GLOBAL
DF_GLOBE, last_ts = mkdf()
DF_EMERG = DF_GLOBE.copy()
TIME_ZONE = 'utc'
TEMP_FLAG = False
DROP_TIME = datetime(year=2025, month=1, day=1).astimezone(timezone.utc)
EMAIL_TIME = datetime(year=2025, month=1, day=1).astimezone(timezone.utc)


def send_emergency_email(plotpath, emailconfig):
    global DF_EMERG, EMAIL_TIME,TIME_ZONE
    EMAIL_TIME = datetime.now().astimezone(timezone.utc)
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    df_plot = DF_EMERG.copy()
    df_plot.index = df_plot.index.tz_convert(TIME_ZONE)
    df_plot.plot(y="Temperature in F", ax=ax)
    ax.set_xlabel(f"Time: ({TIME_ZONE})")
    ax.grid(True)
    now = datetime.now().replace(microsecond=0).astimezone(timezone.utc)
    now_str = "Emergency_Plot" + now.isoformat()[:-6]
    plotstr = str(plotpath.joinpath(now_str + ".png"))
    print("Saving figure to " + plotstr)
    plt.savefig(plotstr, dpi=300)
    plt.close(fig)
    emailconfig["files"] = [plotstr]
    send_email(**emailconfig)


def updatedf(thresh_f, plotpath, emailconfig):
    global DF_GLOBE, TEMP_FLAG, DROP_TIME, DF_EMERG, EMAIL_TIME
    df_i, last_ts = mkdf()
    DF_GLOBE = pd.concat([DF_GLOBE, df_i])

    if df_i['Temperature in F'].iloc[0] < thresh_f and not TEMP_FLAG:
        TEMP_FLAG = True
        DROP_TIME = last_ts
        DF_EMERG = df_i.copy()
    elif df_i['Temperature in F'].iloc[0] >= thresh_f and TEMP_FLAG:
        TEMP_FLAG = False
    elif df_i['Temperature in F'].iloc[0] < thresh_f and TEMP_FLAG:
        DF_EMERG = pd.concat([DF_EMERG, df_i])

    email_check = last_ts > EMAIL_TIME + timedelta(days=1)
    emerg_time = last_ts > DROP_TIME + timedelta(hours=2)
    if email_check and emerg_time and TEMP_FLAG:
        send_emergency_email(plotpath, emailconfig)


def plot_and_save(plotpath, datapath):
    """Plots info from the data frame and saves it.

    Parameters
    ----------
    plotpath : Path
        The location of the saved plots.
    datapath : Path
        The location of the saved data.

    """
    global DF_GLOBE,TIME_ZONE
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    df_plot = DF_GLOBE.copy()
    df_plot.index = df_plot.index.tz_convert(TIME_ZONE)
    df_plot.plot(y="Temperature in F", ax=ax)
    ax.set_xlabel(f"Time: ({TIME_ZONE})")
    ax.grid(True)
    now = datetime.now().replace(microsecond=0).astimezone(timezone.utc)
    now_str = now.isoformat()[:-6]
    plotstr = str(plotpath.joinpath(now_str + ".png"))
    datastr = str(datapath.joinpath(now_str + ".csv"))
    print("Saving figure to " + plotstr)
    plt.savefig(plotstr, dpi=300)
    plt.close(fig)
    print("Saving data to " + datastr)
    DF_GLOBE.to_csv(datastr)
    DF_GLOBE, last_ts = mkdf()


def run_schedule(thresh_f, revisit_time, plottod, plotdir, datadir, yamlconfig):
    global TIME_ZONE
    print(f"Revist Time: {revisit_time} s")
    print(f"Plot Time of Day: {plottod} ")
    print(f"Plot save directory: {plotdir}")
    print(f"Data save directory: {datadir}")
    plotpath = Path(plotdir)
    datapath = Path(datadir)
    with open(yamlconfig, "r") as file:
        configdict = yaml.safe_load(file)
    emailconfig = configdict["emergency_email"]
    TIME_ZONE = configdict.get('timezone',"utc")
    update_job = schedule.every(revisit_time).seconds.do(
        updatedf, thresh_f=thresh_f, plotpath=plotpath, emailconfig=emailconfig
    )
    job = (
        schedule.every()
        .day.at(plottod)
        .do(
            plot_and_save,
            plotpath=plotpath,
            datapath=datapath,
        )
    )
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    args_commd = parse_command_line()
    arg_dict = {k: v for k, v in args_commd._get_kwargs() if v is not None}
    import signal

    # handle SIGTERM (getting killed) gracefully by calling sys.exit
    def sigterm_handler(signal, frame):
        print("Killed")
        sys.stdout.flush()
        sys.exit(128 + signal)

    signal.signal(signal.SIGTERM, sigterm_handler)
    run_schedule(**arg_dict)
# save_to_pandas(500, 86400, "~/weatherplots", "~/weatherdata")
