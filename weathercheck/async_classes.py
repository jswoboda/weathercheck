from pathlib import Path
import ssl
import platform
from typing import Optional

import dataclasses
from dataclasses import dataclass, asdict, field
import aiomqtt
from datetime import datetime, timedelta
import yaml


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


# ── MQTT configuration ────────────────────────────────────────────────────────
@dataclass
class MQTTConfig:
    """
    MQTT broker connection parameters and all topic names used by the system.
    Serialised to / deserialised from  configs/mqtt.yaml.
    """

    broker: str = "localhost"
    """Broker hostname or IP address."""

    port: int = 1883
    """TCP port.  1883 = plain MQTT  |  8883 = MQTT over TLS."""

    keepalive: int = 300
    """MQTT keepalive heartbeat interval (seconds)."""
    tls: TLSConfig = field(default_factory=TLSConfig)
    client_id: str = platform.node()


#     # ── Topics ────────────────────────────────────────────────────────────────
#     command_topic: str = "schedule/command"
#     """
#     Publisher subscribes here.
#     Clients POST  { start_time, repeat, csv_file }  JSON to trigger a schedule.
#     """
#
#     data_topic: str = "schedule/data"
#     """Publisher publishes encoded DataFrame + metadata here; subscribers consume it."""
#
#     ack_topic: str = "schedule/ack"
#     """Subscribers publish QoS-1 acknowledgements here; publisher logs them."""
#
#     list_topic_prefix: str = "schedule/list"
#     """
#     Subscribers publish their schedule inventory to
#     ``<list_topic_prefix>/<hostname>`` when queried via
#     ``cmd/<hostname>/schedule``.
# """
@dataclass
class AppConfig:
    broker_host: str = "localhost"
    broker_port: int = 8883
    tls: TLSConfig = field(default_factory=TLSConfig)
    log_folder: Optional[Path] = None


# ── Internal YAML helper ──────────────────────────────────────────────────────
def _load_yaml(path: str | Path, label: str) -> dict:
    """Read *path* as YAML and return the top-level mapping."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"{label} YAML file not found: {p}")
    with p.open() as fh:
        return yaml.safe_load(fh) or {}


# ── Public loaders ────────────────────────────────────────────────────────────
def load_mqtt_config(path: str | Path) -> MQTTConfig:
    """
    Instantiate :class:`MQTTConfig` from a YAML file.

    Unknown keys are silently ignored.
    Keys whose value is ``null`` fall back to the dataclass default.

    Raises
    ------
    FileNotFoundError : *path* does not exist.
    """
    raw = _load_yaml(path, "MQTT config")
    known = {f.name for f in dataclasses.fields(MQTTConfig)}
    return MQTTConfig(**{k: v for k, v in raw.items() if k in known and v is not None})


def load_tls_config(path: str | Path):
    """
    Instantiate :class:`~tls_utils.TLSConfig` from a YAML file.

    The TLSConfig import is deferred to avoid a module-level circular
    dependency between  config ↔ tls_utils.

    Raises
    ------
    FileNotFoundError : *path* does not exist.
    """

    raw = _load_yaml(path, "TLS config")
    known = {f.name for f in dataclasses.fields(TLSConfig)}
    return TLSConfig(**{k: v for k, v in raw.items() if k in known})
