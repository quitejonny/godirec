import logging
import logging.config
from pkg_resources import resource_filename
import godirec.gui


__version__ = '0.1'


def run_gui():
    godirec.gui.run_gui()


_log_conf_file = resource_filename(__name__, "data/log/log.conf")
logging.config.fileConfig(_log_conf_file, disable_existing_loggers=False)
logging.info("Logging loaded")
