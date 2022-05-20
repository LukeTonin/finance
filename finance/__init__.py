from os.path import dirname, abspath

ROOT_DIR = dirname(abspath(__file__))

from finance.config.logging import configure_logger

configure_logger()