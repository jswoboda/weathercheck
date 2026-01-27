"""MQTT material for publishing and subscribing.
Derived from https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
"""

import json
import logging
import random
import time
from datetime import datetime

from paho.mqtt import client as mqtt_client


def connect_mqtt(
    broker,
    port,
    client_id=f"python-mqtt-{random.randint(0, 1000)}",
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


def subscribe(client: mqtt_client, topic: str):
    #
    # ------------------------------
    # mqtt returns the message here
    # ------------------------------
    #
    def on_message(client, userdata, msg_in):
        msg_decode = msg_in.payload.decode()
        try:
            msg_dejson = json.loads(msg_decode)
        except:
            msg_dejson = None

        if msg_dejson == None:
            msg_dejson = msg_decode
        # endif no dejson
        print(f"Received `{msg_dejson}` from `{msg_in.topic}` topic")

        err_f, inDict = mqtt2dict(msg_dejson)

        if not err_f:
            err_f = decode_uptime(inDict)
            # endif

        client.subscribe(topic)
        client.on_message = on_message


def mqtt2dict(msg):
    """"""
    err_f = False  # init return variables
    respDict = None

    keystr = "messages:"  # find known prefix
    index = msg.find(keystr)
    if index < 0:
        emsg = "config: prefix '%s' not found in:'%s'" % (keystr, msg)
        print(emsg)
        err_f = True
    else:
        evalStr = msg[index + len(keystr) :]  # strip prefix
        evalStr = evalStr.strip()  # strip whitespace
    try:
        respDict = eval(evalStr)  # eval dict-as-string to dict
    except Exception as eobj:
        print("Exception:", eobj)
        emsg = "config: dictionary expected: %s" % (evalStr)
        print(emsg)
        err_f = True
    # end else

    return err_f, respDict


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


def on_disconnect(client, userdata, flags, reason_code, properties):
    """The function for disconneting"""
    # logging.info("Disconnected with result code: %s", rc)
    FIRST_RECONNECT_DELAY = 1
    RECONNECT_RATE = 2
    MAX_RECONNECT_COUNT = 12
    MAX_RECONNECT_DELAY = 60

    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        # logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            # logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    # logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
