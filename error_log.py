import logging

logger = logging.getLogger("mainLog")
fh = logging.FileHandler("mainLog.log")
logger.addHandler(fh)

# logger.info("program start")

def info(msg : object):
    logger.info(msg)

def warning(msg : object):
    logger.warning(msg)

def exception(msg : object):
    logger.exception(msg)

def error(msg : object):
    logger.error(msg)