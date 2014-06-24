# import logging
# import logging.config
import sys
from PyQt4 import QtGui
import os.path
import pkg_resources
import json
import godirec.gui


__version__ = '0.1'


def resource_stream(package, path):
    if hasattr(sys, "frozen"):
        folder = os.path.dirname(sys.argv[0])
        filename = os.path.join(folder, __name__, path)
        return open(filename, 'rb')
    else:
        return pkg_resources.resource_stream(package, path)


def resource_string(package, path):
    with resource_stream(package, path) as f:
        data = f.read()
    return data


# config_str = resource_string(__name__, "data/log/config.json").decode('utf-8')
# logging.config.dictConfig(json.loads(config_str))
# logging.info("Logging loaded")
