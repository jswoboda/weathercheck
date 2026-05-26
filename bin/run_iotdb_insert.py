import time

from schedule import every, repeat, run_pending

from weathercheck import bme280_dict, get_system_dict, iotdb_session

ip = "127.0.0.1"
port_ = "6667"
username_ = "root"
password_ = "root"
sys_name, sys_info = get_system_dict()
SYS_SESH = iotdb_session(
    ip, port_, username_, password_, sys_info, "sys_info", "root.daytest"
)
ENV_SESH = iotdb_session(
    ip, port_, username_, password_, sys_info, "env_info", "root.daytest"
)


@repeat(every(1).minutes)
def insert_system_info():
    global SYS_SESH
    sys_name, sys_info = get_system_dict()
    SYS_SESH.insert_data(sys_info)


@repeat(every(30).minutes)
def insert_env_info():
    global ENV_SESH
    bmedict = bme280_dict()
    dt = bmedict["Time"]
    del bmedict["Time"]
    bmedict["timestamp"] = dt.timestamp()
    ENV_SESH.insert_data(bmedict)


def run_schedule():
    while True:
        run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_schedule()
