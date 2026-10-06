#!python
""""""
import os
import json
from jsonargparse import ActionConfigFile, ArgumentParser

import sys
from loguru import logger
from pymongo import MongoClient, AsyncMongoClient
import ssl
from pathlib import Path
from dataclasses import asdict, dataclass, field
from typing import Optional
import aiomqtt
import anyio


from weathercheck import (
    TLSConfig,
    MQTTConfig,
    build_tls_params,
    AppConfig
)

@dataclass
class MongoConfig:
    """Mongo db configuration"""

    host: str = "127.0.0.1"
    port: int = 27017
    connect = True
    username: Optional[str] = ""
    password: Optional[str] = ""

# ── MQTT message handler ──────────────────────────────────────────────────────






async def _handle_mqtt_message(
    message,
    mongo_cl,
) -> None:
    """
    dt/<programname>/<subject>/<systemname>/<info>
    """

    db_list = mongo_cl.list_database_names()
    mongo_db_name = "home_monitor"
    time_series_options = {
        "timeField": "timestamp",
        "metaField": "meta",
        "granularity": "seconds",
    }


    try:
        topic = message.topic
        topic_parts = topic.split("/")
        meta = {f"node": topic_parts[3]}
        mongo_db_name = topic[1]
        mongo_col_name = topic[2]
        if mongo_db_name not in db_list:
            # The database doesn't exist, so we attempt to create it by creating a collection
            db = mongo_cl[mongo_db_name]
            try:
                await db.create_collection(mongo_col_name, timeseries=time_series_options)
                logging.info(f"Database and collection '{mongo_col_name}' created.")
            except:
                logging.warning(f"Collection '{mongo_col_name}' already exists.")
        else:
            logging.warning(f"Database '{mongo_db_name}' already exists.")

        db = mongo_cl[mongo_db_name]
        collection = db[mongo_col_name]

        payload = json.loads(message.payload.decode())

        payload["meta"] = meta
        await collection.insert_one(payload)

    except json.JSONDecodeError:
        print(f"# MQTT bad JSON payload: {message.payload!r}")
    except Exception as exc:
        print(f"# MQTT handler error: {exc}")


async def mqtt_listener(
    mqtt_cfg: MQTTConfig,
    mg_cfg: MongoConfig
) -> None:
    """Connect to broker, subscribe, and process commands — reconnects on error."""
    tls_params = build_tls_params(mqtt_cfg.tls)
    tls_label = "TLS" if tls_params else "plain"

    cl_dict = asdict(mg_cfg)
    if mg_cfg.username == "":
        del cl_dict["username"]
        del cl_dict["password"]
    mongo_cl = AsyncMongoClient(**cl_dict)
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
                    await _handle_mqtt_message(message, mongo_cl)

        except aiomqtt.MqttError as exc:
            print(f"# MQTT error: {exc} — reconnecting in {mqtt_cfg.keepalive}s …")
            await anyio.sleep(mqtt_cfg.keepalive)




def build_parser() -> ArgumentParser:
    p = ArgumentParser(
        description="Mongo db listener for mqtt messages."
    )
    p.add_argument("--config", action=ActionConfigFile, help="YAML / JSON config file")
    p.add_class_arguments(TLSConfig, nested_key="tls")
    p.add_class_arguments(MongoConfig,nested_key="mongo")
    p.add_argument(
        "--broker_host",
        type=str,
        default="localhost",
        help="MQTT broker hostname or IP",
    )
    p.add_argument(
        "--broker_port",
        type=int,
        default=8883,
        help="MQTT broker port (default 8883 for TLS)",
    )

    return p

async def main(cfg: MQTTConfig, mgcfg: MongoConfig) -> None:


    async with anyio.create_task_group() as tg:
        tg.start_soon(mqtt_listener, cfg, mgcfg, tg)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = build_parser()
    ns = parser.parse_args()

    tls = TLSConfig(
        ca_cert=ns.tls.ca_cert,
        certfile=ns.tls.certfile,
        keyfile=ns.tls.keyfile,
        verify_hostname=ns.tls.verify_hostname,
    )
    mqcfg = MQTTConfig(
        broker=ns.broker_host,
        port=ns.broker_port,
        tls=tls,
    )
    mgcfg: MongoConfig = ns.mongo

    anyio.run(main, mqcfg,mgcfg)
