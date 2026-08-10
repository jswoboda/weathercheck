import json
import platform
from datetime import datetime
from copy import copy
from .bme280_basic import bme280_dict
from .mqtt_tools import connect_mqtt, publish_dict
from .systeminfo import get_system_dict


def bme280_scrape(client, sys_name=None, topic_suf="BME280reading"):
    """Gets current environment measurements from bme280 and publishes them to MQTT.

          - RECORDER_ANNOUNCE_TOPIC=dt/vsword/{service.name}/{service.node_id}/announce
          - RECORDER_COMMAND_TOPIC=cmd/vsword/{service.name}/{service.node_id}/request
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
        sys_name = platform.node()
    topic = "dt/weathercheck/" + topic_suf + "/" + sys_name + "/" + "data"
    bme_data = bme280_dict()
    bme_copy = copy(bme_data)
    for ikey, iobj in bme_copy.items():
        if isinstance(iobj, datetime):
            bme_data["timestamp"] = iobj.timestamp()
            del bme_data[ikey]
    bmejson = json.dumps(bme_data)
    print(topic)
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
    topic = "dt/weathercheck/" + topic_suf + "/" + sys_name + "/status"
    sys_copy = copy(sys_data)
    for ikey, iobj in sys_copy.items():
        if isinstance(iobj, datetime):
            sys_data["timestamp"] = iobj.timestamp()
            del sys_data[ikey]
    sysjson = json.dumps(sys_data)
    return publish_dict(client, topic, sysjson)
