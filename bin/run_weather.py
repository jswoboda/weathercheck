#!python

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
import pandas as pd

from weathercheck import get_bme280_data, mkdf, sys_stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
        "-r",
        "--revisit_time",
        dest="revisit_time",
        help="Number of seconds to revisit the measurmeent.",
        required=True,
        type=int,
    )
    parser.add_argument(
        "-p",
        "--plot_revist",
        dest="plot_revist",
        help="Number of seconds to revist the ploting and savedata.",
        required=True,
        type=int,
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
    if str_input is None:
        return parser.parse_args()
    return parser.parse_args(str_input)


def plot_and_save(df_in, plotpath, datapath):
    """Plots info from the data frame and saves it.

    Parameters
    ----------
    df_in : pd.DataFrame
        The data frame that will be saved and plotted.
    plotpath : Path
        The location of the saved plots.
    datapath : Path
        The location of the saved data.

    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    df_in.plot(y="Temperature in F", ax=ax)
    ax.grid(True)
    now = datetime.now().replace(microsecond=0).astimezone(timezone.utc)
    now_str = now.isoformat()[:-6]
    plotstr = str(plotpath.joinpath(now_str + ".png"))
    datastr = str(datapath.joinpath(now_str + ".csv"))
    print("Saving figure to " + plotstr)
    plt.savefig(plotstr, dpi=300)
    plt.close(fig)
    print("Saving data to " + datastr)
    df_in.to_csv(datastr)


def save_to_pandas(revisit_time, plot_revist, plotdir, datadir):
    """Performs the scheduling and saving the data. This function will run perminately.

    Parameters
    ----------
    revist_time : int
        Number of seconds for each revisit.
    plot_revisit : int
        Number of seconds for each revisit.
    plotdir : str
        Location of where the plots will be kept.
    datadir : str
        Location of the csv data.
    """
    print(f"Revist Time: {revisit_time} s")
    print(f"Plot Time: {plot_revist} s")
    print(f"Plot save dir{plotdir}")
    print(f"Data save dir{datadir}")
    plotpath = Path(plotdir)
    datapath = Path(datadir)
    td = timedelta(seconds=revisit_time)
    plt_revist = timedelta(seconds=plot_revist)
    df_w, last_ts = mkdf()
    next_read = last_ts + td
    next_plot = last_ts + plt_revist
    now = datetime.now().astimezone(timezone.utc)

    while True:
        # add to the dataframe
        if now > next_read:
            df_i, last_ts = mkdf()
            next_read = last_ts + td
            df_w = pd.concat([df_w, df_i])
        # save out the dataframe
        if now > next_plot:
            plot_and_save(df_w, plotpath, datapath)
            df_w, last_ts = mkdf()
            next_read = last_ts + td
            next_plot = last_ts + plt_revist
        time.sleep(1)
        now = datetime.now().astimezone(timezone.utc)


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
    save_to_pandas(**arg_dict)
# save_to_pandas(500, 86400, "~/weatherplots", "~/weatherdata")
