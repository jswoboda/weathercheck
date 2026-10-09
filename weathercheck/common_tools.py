#!python
import sys
from pathlib import Path

import yamale
from loguru import logger
from datetime import datetime, timezone
from typing import Dict, Any

# ───────────────────────────────────────────────────────────────────────────
# Timestamp precision helpers
# ───────────────────────────────────────────────────────────────────────────

#: Maps a plugin-declared precision string to the MQTT payload field name.
PRECISION_FIELD = {
    "s": "timestamp",
    "ms": "timestampms",
    "us": "timestampus",
    "ns": "timestampns",
}

#: Maps a precision string to the multiplier used to convert POSIX seconds
#: into an integer timestamp of that precision.
PRECISION_MULT = {"s": 1, "ms": 1_000, "us": 1_000_000, "ns": 1_000_000_000}


def build_timestamp_payload(precision: str, moment: datetime) -> Dict[str, int]:
    """Build the integer timestamp field for an MQTT payload.

    Parameters
    ----------
    precision : str
        One of ``"s"``, ``"ms"``, ``"us"``, ``"ns"``. Unknown values fall
        back to whole seconds.
    moment : datetime.datetime
        A timezone-aware UTC instant.

    Returns
    -------
    dict
        A single-key dictionary, e.g. ``{"timestampms": 1699999999123}``.
    """
    field_name = PRECISION_FIELD.get(precision, "timestamp")
    mult = PRECISION_MULT.get(precision, 1)
    return {field_name: int(moment.timestamp() * mult)}


def extract_timestamp(payload: Dict[str, Any], precision: str) -> datetime:
    """Recover a UTC ``datetime`` from an ack/backlog payload.

    Parameters
    ----------
    payload : dict
        A decoded JSON payload expected to contain the field named per
        :data:`PRECISION_FIELD`.
    precision : str
        The precision string used to pick the field name / multiplier.

    Returns
    -------
    datetime.datetime
        UTC datetime; the Unix epoch if the field is missing (meaning
        "replay everything").
    """
    field_name = PRECISION_FIELD.get(precision, "timestamp")
    mult = PRECISION_MULT.get(precision, 1)
    raw = payload.get(field_name)
    if raw is None:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromtimestamp(raw / mult, tz=timezone.utc)


def get_config_loc():
    """Gets the location of the configuration directory.

    Returns
    -------
    config_path : Path
        The configuration directory path.
    """
    mod_path = Path(__file__).parent.parent
    config_path = mod_path.joinpath("config")
    return config_path


def read_yaml_config(yamlfile, schemafile=None):
    """Parse config files.

    The function parses the given file and returns a dictionary with the values.

    Note
    ----
    Sections should be named: siminfo and channels

    Parameters
    ----------
    yamlfile : str
        The name of the file to be read including path.

    Returns
    -------
    objs : dictionay
        Dictionary with name given by [Section] each of which contains.
    """

    dirname = Path(__file__).expanduser().parent
    if schemafile is None:
        schemafile = dirname / "configschema.yaml"
    schema = yamale.make_schema(schemafile)
    data = yamale.make_data(yamlfile)
    d1 = yamale.validate(schema, data)

    return data[0][0]


def setuplog(logfile=None, serializelogfile=False):
    """Set up the logger object.

    Parameters
    ----------
    logfile : str
        Name of the log file.
    serializelogfile : bool
        Turn the logfile in json strings.

    Returns
    -------
    logger : logger
        Logger object.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="[<red>{time:HH:mm:ss}</red>] >><yellow>{level}</yellow>:<cyan>{message}</cyan>",
    )
    if logfile:
        logger.add(
            logfile,
            serialize=serializelogfile,
        )
    return logger
