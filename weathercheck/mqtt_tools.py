"""MQTT material for publishing and subscribing.
Derived from https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
"""

import json
import logging
import random
import time
from datetime import datetime

from paho.mqtt import client as mqtt_client

client_id = f"python-mqtt-{random.randint(0, 1000)}"


def connect_mqtt(
    broker,
    port,
    client_id,
    ca_certs_in=None,
    certfile_in=None,
    keyfile_in=None,
    keepalive=2400,
):
    """Returns a client object to connect to MQTT.
    Parameters
    ----------
    broker : str
        Broker IP or address.
    port : int
        Port number for the broker.
    client_id : str
        Id of the MQTT client.

    Returns
    -------
    client : mqtt.client
        The client object you can use to publish.
    """

    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    # Set Connecting Client ID
    client = mqtt_client.Client(
        client_id=client_id,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    )
    if ca_certs_in is not None:
        client.tls_set(ca_certs=ca_certs_in, certfile=certfile_in, keyfile=keyfile_in)

    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port, keepalive)
    client.on_disconnect = on_disconnect
    return client


def publish_dict(client, topic, jsonmsg):
    """Publishes a dictionary and will check for datetime objects and change them to timestamps.

    Parameters
    ----------
    client : mqtt.client
        The client object you can use to publish.
    topic : str
        The topic string.
    msgdict : dict
        A flat dictionary made of just simple objects.

    Returns
    -------
    : bool
        Did the publishing succeed.
    """

    # for ikey, iobj in msgdict.items():
    #     if isinstance(iobj, datetime):
    #         msgdict[ikey] = iobj.timestamp()
    # jsonmsg = json.dumps(msgdict)
    result = client.publish(topic, jsonmsg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        return True
    else:
        return False


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60


def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
