import platform
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


def get_system_dict():
    """Get a dictionary holding all of the system info at the moment.

    Returns
    -------
    sys_name : str
        Name of the system from the platform module
    sys_info : dict
        Dictionary holding the system information.
    """
    sys_name = platform.node()
    disk_info = get_disk_use()
    disk_names = ["disksizeGB", "useddiskGB", "freediskGB"]
    sys_info = {ikey: iobj for ikey, iobj in zip(disk_names, disk_info)}
    sys_list = sys_stats()
    sys_name = ["uptime", "cpuuse", "rampercent", "ramuseGB"]
    sys_dict = {ikey: iobj for ikey, iobj in zip(sys_name, sys_list)}
    sys_info.update(sys_dict)
    return sys_name, sys_info
