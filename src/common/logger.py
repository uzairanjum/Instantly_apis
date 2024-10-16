import logging

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:  # Check if handlers already exist
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Prevent the logger from propagating to the root logger
    return logger