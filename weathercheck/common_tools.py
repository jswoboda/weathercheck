#!python
from pathlib import Path

import yamale
from loguru import logger


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


def setuplog(logfile=None, file_name=__file__, serializelogfile=False):
    """Set up the logger object.

    Parameters
    ----------
    logfile : str
        Name of the log file.

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
