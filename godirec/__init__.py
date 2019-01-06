# GodiRec is a program for recording a church service
# Copyright (C) 2014 Daniel Supplieth and Johannes Roos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import logging.config
import sys
import os
import os.path
if not hasattr(sys, "frozen"):
    import pkg_resources
import json
# for convenience all error class can be accessed from godirec module directly
from godirec.errors import *


__version__ = '0.6.3'


class Callback(object):

    def __init__(self, func=lambda x: None, *args):
        self.set_func(func, *args)

    def __nonzero__(self):
        zero_func = lambda x: None
        if self._func == zero_func:
            return False
        else:
            return True

    def set_func(self, func, *args):
        self._func = func
        self._args = args

    def emit(self, *args):
        complete_args = self._args + args
        self._func(complete_args)


def get_config_file():
    if sys.platform == 'win32':
        config_dir = os.path.join(os.getenv('APPDATA'), 'godirec')
    else:
        config_dir = os.path.join(os.getenv('HOME'), '.godirec')
    config_file = os.path.join(config_dir, 'setting.ini')
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
        config_str = resource_string(__name__, "data/log/config.json")
        config_str = config_str.decode('utf-8')
        with open(config_file, 'w') as f:
            f.write(config_str)
        change_log_dir(config_dir, config_file)
    return config_file


def get_log_dir():
    with open(config_file, 'r') as f:
        config = json.load(f)
    info_filename = config['handlers']['info_file_handler']['filename']
    return os.path.dirname(info_filename)


def change_log_dir(log_dir, config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    # replace log file location with new log file location
    for i in ('error', 'info'):
        log_file = os.path.join(log_dir, i+'.log')
        config['handlers'][i+'_file_handler']['filename'] = log_file
    with open(config_file, 'w') as f:
        json.dump(config, f)


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


config_file = get_config_file()
with open(config_file, 'r') as data_file:
    logging.config.dictConfig(json.load(data_file))
logging.info("Logging loaded")
