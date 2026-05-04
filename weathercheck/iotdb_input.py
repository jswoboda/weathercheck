import json
import sys
from datetime import UTC, datetime

import numpy as np
from iotdb.dbapi import connect
from iotdb.Session import Session
from iotdb.utils.IoTDBConstants import Compressor, TSDataType, TSEncoding
from paho.mqtt import client as mqtt_client

# def get_iotdb_datatype(data_obj):


def get_iotdb_datatype(obj):
    reflist = [
        (TSDataType.BOOLEAN, [bool, np.bool_]),
        (TSDataType.INT32, [int, np.int32]),
        (TSDataType.INT64, [np.int64]),
        (
            TSDataType.FLOAT,
            [float, np.float64, np.float32],
        ),
        (TSDataType.DOUBLE, [np.double]),
        (TSDataType.TEXT, [np.char, np.string_, np.str_s, str]),
    ]


class iotdb_session(object):
    """Ties the MQTT Topics to the iotdb storage"""

    def __init__(
        self,
        ip,
        port_,
        username_,
        password_,
        measurements_list_,
        data_type_list_,
        ts_name,
        store_group,
        device_id,
        fetch_size=1024,
        zone_id="UTC",
        enable_redirection=False,
    ):
        self.sesh = Session(ip, port_, username_, password_, fetch_size, zone_id)
        self.sesh.open(False)
        self.sesh.set_storage_group(store_group)
        self.ts_name = ts_name
        self.store_group = store_group
        self.measurements = measurements_list_
        self.datatypes = data_type_list_
        encoding_lst_ = [TSEncoding.PLAIN for _ in range(len(data_type_list_))]
        compressor_lst_ = [Compressor.SNAPPY for _ in range(len(data_type_list_))]
        self.sesh.create_aligned_time_series(
            store_group + "." + ts_name,
            measurements_list_,
            data_type_list_,
            encoding_lst_,
            compressor_lst_,
        )

    def insert_data(self, topic, datadict):
        meas_list = []
        d_list = []
        val_list = []
        cur_ts = None
        for ikey, iobj in datadict.items():
            if "timestamp" in ikey:
                cur_ts = iobj

            elif ikey in self.measurements:
                cur_ind = self.measurements.index(ikey)
                meas_list.append(ikey)
                d_list.append(self.datatypes[cur_ind])
                val_list.append(iobj)
        if cur_ts is None:
            cur_ts = int(datetime.now(UTC).timestamp())
        self.sesh.insert_aligned_record(
            self.store_group + "." + self.ts_name,
            int(cur_ts * 1e3),  # time stamps are for millisecondss
            meas_list,
            d_list,
            val_list,
        )


def db_connect(dbname="root.db", username="root", password="root"):
    print("connecting to db,user:", dbname, username)

    try:
        conn = connect(
            "eclipse-control.haystack.mit.edu",
            "6667",
            username,
            password,
            fetch_size=1024,
            zone_id="UTC+8",
            sqlalchemy_mode=False,
        )  # open a connection
    except Exception as eobj:
        print("Error - connect fails:", eobj)
        print("Is the IoTDB server running?\n")
        sys.exit()
    # end exception

    cursor = conn.cursor()  # Open a cursor to perform database operations

    return conn, cursor


def subscribe(client: mqtt_client, topic: str):
    def on_message(client, userdata, msg_in):
        msg_decode = msg_in.payload.decode()
        try:
            msg_dejson = json.loads(msg_decode)
        except Exception as e:
            msg_dejson = None
            print(e)

        client.subscribe(topic)
        client.on_message = on_message
