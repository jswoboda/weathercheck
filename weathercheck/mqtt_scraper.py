import json
import platform
from datetime import datetime

from .bme280_basic import bme280_dict
from .mqtt_tools import connect_mqtt, publish_dict
from .systeminfo import get_system_dict


def bme280_scrape(client, sys_name=None, topic_suf="BME280reading"):
    """Gets current environment measurements from bme280 and publishes them to MQTT.

    Parameters
    ----------
    client : mqtt.client
        Object to connect to MQTT.
    sys_name : str
        System name for the mqtt topic
    topic_suf : str
        The final part of the topic

    Returns
    -------
    : bool
        Was the transmisison a success.

    """
    if sys_name is None:
        sys_name = platform.node
    topic = sys_name + "/" + "topic"
    bme_data = bme280_dict()
    for ikey, iobj in bme_data.items():
        if isinstance(iobj, datetime):
            bme_data[ikey] = iobj.timestamp()
    bmejson = json.dumps(bme_data)
    return publish_dict(client, topic, bmejson)


def sys_scrape(client, sys_name=None, topic_suf="compute_status"):
    """Gets current systems stats and publishes them to MQTT.

    Parameters
    ----------
    client : mqtt.client
        Object to connect to MQTT.
    sys_name : str
        System name for the mqtt topic
    topic_suf : str
        The final part of the topic

    Returns
    -------
    : bool
        Was the transmisison a success.
    """
    sys_read_name, sys_data = get_system_dict()

    if sys_name is None:
        sys_name = sys_read_name
    topic = sys_name + "/" + "topic"
    for ikey, iobj in sys_data.items():
        if isinstance(iobj, datetime):
            sys_data[ikey] = iobj.timestamp()
    sysjson = json.dumps(sys_data)
    return publish_dict(client, topic, sysjson)
