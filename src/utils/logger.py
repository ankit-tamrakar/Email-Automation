import logging
from datetime import datetime


current_day = datetime.now().strftime("%Y%m%d")
file_handler = logging.FileHandler(f"logs/email_automation_{current_day}.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s'))

def setlog(name=__name__):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    
    return logger