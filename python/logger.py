import logging
from logging.handlers import RotatingFileHandler
from config import config

logger = logging.getLogger(__name__)
try:
    logfile = config["Logging"]["FilePath"]
except:
    logfile = 'rttserver.log'

try:
    maxsize = config["Logging"]["MaxSize"]
    if maxsize < 500 * 1024:
        maxsize = 500 * 1024 #500kb
except:
    maxsize = 1 * 1024* 1024 #1mb

try:
    maxfiles = config["Logging"]["MaxFiles"]
except:
    maxfiles = 5
    
LOGLEVEL = logging.DEBUG
if config["Logging"]["Debug"]:
	LOGLEVEL = logging.DEBUG
logger.setLevel(LOGLEVEL)

#file logger
lh = RotatingFileHandler(logfile, maxBytes=maxsize, backupCount=maxfiles)
lh.setLevel(LOGLEVEL)
fmt = logging.Formatter('%(asctime)s [%(name)s][%(levelname)s]: %(message)s', '%m/%d/%Y %I:%M:%S')
lh.setFormatter(fmt)
logger.addHandler(lh)

#Console logger
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL)
ch.setFormatter(fmt)
logger.addHandler(ch)

logger.info("Logging loaded")
if config["Logging"]["Debug"] == "True":
	logger.debug("Debug is set")
