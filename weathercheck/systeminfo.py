import shutil
import time

import psutil


def get_disk_use():
    """Get the disk usage

    Returns
    -------
    totGB : float
        Disk size in GB
    usedGB : float
        Used disk space in GB
    freeGB : float
        Free disk space in GB
    """
    # Fetching disk usage details
    total, used, free = shutil.disk_usage("/")
    totGB = total * 2**-30
    usedGB = used * 2**-30
    freeGB = free * 2**-30
    return totGB, usedGB, freeGB


def sys_stats():
    """Get the system stats

    Returns
    -------
    uptime : float
        Uptime in seconds.
    cpu_use : float
        Percentage of CPU being used.
    ram_per : float
        Percentage of RAM being used.
    ram_usedGB : float
        Same as ram percentage but in GB.

    """
    uptime = time.monotonic()
    cpu_use = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_per = ram.percent
    ram_usedGB = ram.used * 2**-30

    return uptime, cpu_use, ram_per, ram_usedGB
