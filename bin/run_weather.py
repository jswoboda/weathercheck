import time
from datetime import datetime, timedelta, timezone

import matplotlib
import pandas as pd

from weathercheck import get_bme280_data, sys_stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def mkdf():
    colsw = [
        "Temperature in C",
        "Temperature in F",
        "Dewpoint in C",
        "Dewpoint in F",
        "Humidity",
        "Pressure",
        "Time",
    ]
    data_init = get_bme280_data()
    dfdict = {icol: idata for icol, idata in zip(colsw, data_init)}
    ts1 = dfdict["Time"]
    del dfdict["Time"]
    df_w = pd.DataFrame(dfdict, index=[ts1])
    return df_w, ts1


def plot_and_save(df_in):
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    df_in.plot(x="Time", y="Temperature in C", ax=ax)
    plt.savefig("curplot.png", dpi=300)
    plt.close(fig)


def save_to_pandas(revisit_time):
    td = timedelta(seconds=revisit_time)

    df_w, last_ts = mkdf()
    next_read = last_ts + td
    now = datetime.now().astimezone(timezone.utc)

    while True:
        if now > next_read:
            df_i, last_ts = mkdf()
            next_read = last_ts + td
            df_w = pd.concat([df_w, df_i])

        time.sleep(1)
        now = datetime.now().astimezone(timezone.utc)


if __name__ == "__main__":
    save_to_pandas(500)
