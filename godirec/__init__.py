import logging
import logging.config
import sys
from PyQt4 import QtGui
import os.path
import pkg_resources
import json
import godirec.gui


__version__ = '0.1'


def resource_stream(package, path):
    if hasattr(sys, "frozen"):
        return open(resource_filename(package, path), 'rb')
    else:
        return pkg_resources.resource_stream(package, path)


def resource_string(package, path):
    with resource_stream(package, path) as f:
        data = f.read()
    return data


def resource_filename(package, path):
    if hasattr(sys, "frozen"):
        folder = os.path.dirname(sys.argv[0])
        return os.path.join(folder, __name__, path)
    else:
        return pkg_resources.resource_filename(package, path)


config_str = resource_string(__name__, "data/log/config.json").decode('utf-8')
logging.config.dictConfig(json.loads(config_str))
logging.info("Logging loaded")
