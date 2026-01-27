import json
import sys
from datetime import UTC, datetime

from iotdb.dbapi import connect
from iotdb.Session import Session
from iotdb.utils.IoTDBConstants import Compressor, TSDataType, TSEncoding
from paho.mqtt import client as mqtt_client

# def get_iotdb_datatype(data_obj):


class iotdb_session(object):
    """Ties the MQTT Topics to the"""

    def __init__(
        self,
        ip,
        port_,
        username_,
        password_,
        measurements_list_,
        data_type_list_,
        ts_name,
        device_id,
        fetch_size=1024,
        zone_id="UTC",
        enable_redirection=True,
    ):
        self.sesh = Session(
            ip, port_, username_, password_, fetch_size, zone_id, enable_redirection
        )
        self.sesh.open(False)
        self.ts_name = ts_name
        self.measurements = measurements_list_
        self.datatypes = data_type_list_
        encoding_lst_ = [TSEncoding.PLAIN for _ in range(len(data_type_list_))]
        compressor_lst_ = [Compressor.SNAPPY for _ in range(len(data_type_list_))]
        self.sesh.create_aligned_time_series(
            ts_name,
            measurements_list_,
            data_type_list_,
            encoding_lst_,
            compressor_lst_,
        )

    def insert_data(self, datadict):
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
            cur_ts = datetime.now(UTC).timestamp()
        self.sesh.insert_aligned_record(
            self.ts_name, cur_ts, meas_list, d_list, val_list
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
        except:
            msg_dejson = None

        client.subscribe(topic)
        client.on_message = on_message
