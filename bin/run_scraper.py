#!python
import argparse
import sys
import time
from pathlib import Path

import schedule

from weathercheck import bme280_scrape, connect_mqtt, sys_scrape


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
    title = "Runs MQTT scaper"
    shortdesc = "Runs the MQTT scappr."
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
        "-b",
        "--broker",
        dest="broker",
        help="Broker address.",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        help="Port number for the broker.",
        default=8883,
        type=int,
    )
    parser.add_argument(
        "-e",
        "--enrevisit",
        dest="enrevisit",
        help="Publication period for the environment sensors in seconds.",
        default=600,
        type=int,
    )
    parser.add_argument(
        "-s",
        "--sysrevisit",
        dest="sysrevisit",
        help="Publication period for the compute system info in seconds.",
        default=60,
        type=int,
    )
    parser.add_argument(
        "-c",
        "--certfolder",
        dest="certfolder",
        help="Location of the certs",
        default="",
        type=str,
    )
    if str_input is None:
        return parser.parse_args()
    return parser.parse_args(str_input)


BME_FAIL_COUNT = 0
SYS_FAIL_COUNT = 0


def get_certs(certfolder=""):
    if not certfolder:
        return None, None, None
        # ca_certs_in = None
        # certfile_in = None
        # keyfile_in = None

    cert_path = Path(certfolder)
    cert_path.expanduser()
    ca_certs_in = str(cert_path.join("ca.pem"))
    certfile_in = str(cert_path.join("client.pen"))
    keyfile_in = str(cert_path.join("client.key"))
    return ca_certs_in, certfile_in, keyfile_in


def bme_scrape_cont(client):
    global BME_FAIL_COUNT
    result = bme280_scrape(client)
    if result:
        BME_FAIL_COUNT = 0
    else:
        BME_FAIL_COUNT += 1


def sys_scrape_cont(client):
    global SYS_FAIL_COUNT
    result = sys_scrape(client)
    if result:
        SYS_FAIL_COUNT = 0
    else:
        SYS_FAIL_COUNT += 1


def scraper_main(broker, port, enrevisit, sysrevisit, certfolder=""):
    """Runs the Scraper function.

    Parameters
    ----------
    broker : str
        Address of the broker.
    port : int
        Port number for the publisher
    enrevisit : int
        Number of seconds for revisting the sensor.
    sysrevist : int
        Number of seconds for checking the system info.
    certfolder : int
        The folder holding the certs.
    """
    global SYS_FAIL_COUNT, BME_FAIL_COUNT
    client = connect_mqtt(broker, port)

    env_job = schedule.every(enrevisit).seconds.do(bme_scrape_cont, client=client)
    sys_job = schedule.every(sysrevisit).seconds.do(sys_scrape_cont, client=client)
    sys_fail = False
    env_fail = False

    while True:
        schedule.run_pending()
        if SYS_FAIL_COUNT > 3:
            schedule.cancel_job(sys_job)
            sys_fail = True
        if BME_FAIL_COUNT > 3:
            schedule.cancel_job(env_job)
        if sys_fail and env_fail:
            raise Exception("Both scrapers failed.")
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
    scraper_main(**arg_dict)
