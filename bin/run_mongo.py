import os
import json
import sys
from loguru import logging
from pymongo import MongoClient, AsyncMongoClient
import ssl
from pathlib import Path
from dataclasses import asdict, dataclass, field
from typing import Optional
import aiomqtt
import anyio


# ── Config dataclasses ────────────────────────────────────────────────────────
@dataclass
class TLSConfig:
    """TLS certificate paths for the MQTT connection."""

    ca_cert: Optional[Path] = Path(
        "~/keys/ca.pem"
    ).expanduser()  # CA / root certificate
    certfile: Optional[Path] = Path(
        "~/keys/client.pem"
    ).expanduser()  # client certificate
    keyfile: Optional[Path] = Path(
        "~/keys/client.key"
    ).expanduser()  # client private key
    verify_hostname: bool = True


# ── TLS helper ────────────────────────────────────────────────────────────────
def build_tls_params(tls: TLSConfig) -> Optional[aiomqtt.TLSParameters]:
    """
    Build aiomqtt TLS parameters from a TLSConfig. Returns None for a plain (non-TLS) connection.

    Parameters
    ----------
    tls : TLSConfig
        The tls file names

    Returns
    -------
    :aiomqtt.TLSParameters
        The TLS parameters in the right format for the mqtt client
    """
    if not any([tls.ca_cert, tls.certfile, tls.keyfile]):
        return None

    return aiomqtt.TLSParameters(
        ca_certs=str(tls.ca_cert) if tls.ca_cert else None,
        certfile=str(tls.certfile) if tls.certfile else None,
        keyfile=str(tls.keyfile) if tls.keyfile else None,
        cert_reqs=ssl.CERT_REQUIRED if tls.verify_hostname else ssl.CERT_NONE,
    )


@dataclass
class MQTTConfig:
    """MQTT broker connection settings."""

    broker: str = "127.0.0.1"
    port: int = 8883
    reconnect_s: int = 30
    client_id: str = "dbhold"
    tls: TLSConfig = field(default_factory=TLSConfig)


@dataclass
class MongoConfig:
    """Mongo db configuration"""

    host: str = "127.0.0.1"
    port: int = 27017
    connect = True
    username: Optional[str] = ""
    password: Optional[str] = ""


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logging.info("Starting MQTT to MongoDB service")

# Load configuration from environment variables
mongo_host = os.getenv("MONGO_HOST")
mongo_port = int(os.getenv("MONGO_PORT"))  # Convert port to integer
mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")
mongo_database_name = os.getenv("MONGO_DATABASE_NAME")
mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME")

mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))  # Convert port to integer
mqtt_topic = os.getenv("MQTT_TOPIC")


# MongoDB setup
mongo_client = MongoClient(
    host=mongo_host, port=mongo_port, username=mongo_username, password=mongo_password
)

# Check if the database exists
db_list = mongo_client.list_database_names()
if mongo_database_name not in db_list:
    # The database doesn't exist, so we attempt to create it by creating a collection
    db = mongo_client[mongo_database_name]
    try:
        db.create_collection(mongo_collection_name)
        logging.info(f"Database and collection '{mongo_collection_name}' created.")
    except:
        logging.warning(f"Collection '{mongo_collection_name}' already exists.")
else:
    logging.warning(f"Database '{mongo_database_name}' already exists.")


db = mongo_client[mongo_database_name]
collection = db[mongo_collection_name]

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)  # Create a new MQTT client
mqtt_client.username_pw_set(mqtt_user, mqtt_password)  # Set MQTT credentials

# Configure TLS/SSL connection if necessary (uncomment if needed)
mqtt_client.tls_set()


# MQTT setup and event handlers
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe(mqtt_topic)  # Subscribe to the topic from the environment


def on_message(client, userdata, msg):
    try:
        # Convert message payload to string and then to JSON
        message_str = msg.payload.decode("utf-8")
        message_data = json.loads(message_str[:-1])
        # Insert the message into MongoDB
        logging.info(f"Inserting message into MongoDB: {message_data}")
        message_data["topic"] = msg.topic

        collection.insert_one(message_data)
    except Exception as e:
        logging.error(f"Error handling message: {e}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(mqtt_host, mqtt_port, 60)  # Connect to the MQTT broker
    mqtt_client.loop_forever()  # Start processing MQTT messages
except Exception as e:
    logging.error(f"Error connecting to MQTT broker: {e}")


# ── MQTT message handler ──────────────────────────────────────────────────────
async def _handle_mqtt_message(
    message,
    mongo_collection,
) -> None:
    """
    Supported actions — JSON payload on recorder/schedule:

        Add schedule:    {"action": "add",      "start": "yyyy-mm-ddTHH:MM:00Z", 'end': "yyyy-mm-ddTHH:MM:00Z" }
        Remove schedule: {"action": "remove",   "start": "yyyy-mm-ddTHH:MM:00Z", 'end': "yyyy-mm-ddTHH:MM:00Z"}
        List schedules:  {"action": "list"}
        Run now:         {"action": "run_now",   'end': "yyyy-mm-ddTHH:MM:00Z"}
    """
    try:
        topic = message.topic
        topic_parts = topic.split("/")
        meta = {"subject": topic[2], "node": topic_parts[3]}

        payload = json.loads(message.payload.decode())

        payload["meta"] = meta
        mongo_collection.insert_one(payload)

    except json.JSONDecodeError:
        print(f"# MQTT bad JSON payload: {message.payload!r}")
    except Exception as exc:
        print(f"# MQTT handler error: {exc}")


# ── MQTT listener ─────────────────────────────────────────────────────────────
async def mqtt_listener(
    mongo_cfg: MongoConfig,
    mqtt_cfg: MQTTConfig,
) -> None:
    """Connect to broker, subscribe, and process commands — reconnects on error."""
    cl_dict = asdict(mongo_cfg)
    if mongo_cfg.username == "":
        del cl_dict["username"]
        del cl_dict["password"]
    mongo_cl = AsyncMongoClient(**cl_dict)
    # Check if the database exists
    db_list = mongo_cl.list_database_names()
    mongo_db_name = "home_monitor"
    time_series_options = {
        "timeField": "timestamp",
        "metaField": "meta",
        "granularity": "seconds",
    }
    mongo_col_name = "network"
    if mongo_db_name not in db_list:
        # The database doesn't exist, so we attempt to create it by creating a collection
        db = mongo_cl[mongo_db_name]
        try:
            db.create_collection(mongo_col_name, timeseries=time_series_options)
            logging.info(f"Database and collection '{mongo_col_name}' created.")
        except:
            logging.warning(f"Collection '{mongo_col_name}' already exists.")
    else:
        logging.warning(f"Database '{mongo_db_name}' already exists.")

    db = mongo_client[mongo_db_name]
    collection = db[mongo_col_name]
    tls_params = build_tls_params(mqtt_cfg.tls)
    cparams = dict(
        hostname=mqtt_cfg.broker,
        port=mqtt_cfg.port,
        identifier=mqtt_cfg.client_id,
        tls_params=tls_params,
    )
    while True:
        try:
            async with aiomqtt.Client(**cparams) as client:
                await client.subscribe("dt/#")

                async for message in client.messages:
                    await _handle_mqtt_message(message, collection)

        except aiomqtt.MqttError as exc:
            print(f"# MQTT error: {exc} — reconnecting in {mqtt_cfg.reconnect_s}s …")
            await anyio.sleep(mqtt_cfg.reconnect_s)


async def mqtt_listener_simple(
    mqtt_cfg: MQTTConfig,
) -> None:
    """Connect to broker, subscribe, and process commands — reconnects on error."""
    tls_params = build_tls_params(mqtt_cfg.tls)
    tls_label = "TLS" if tls_params else "plain"

    while True:
        try:
            async with aiomqtt.Client(
                hostname=mqtt_cfg.broker,
                port=mqtt_cfg.port,
                identifier=mqtt_cfg.client_id,
                tls_params=tls_params,
            ) as client:
                await client.subscribe("dt/#")
                print(
                    f"# MQTT connected ({tls_label})"
                    f" → {mqtt_cfg.broker}:{mqtt_cfg.port}"
                )
                async for message in client.messages:
                    print(f"{message.topic}{message.payload}")

        except aiomqtt.MqttError as exc:
            print(f"# MQTT error: {exc} — reconnecting in {mqtt_cfg.reconnect_s}s …")
            await anyio.sleep(mqtt_cfg.reconnect_s)
