import logging


def build_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
    logger.handlers.clear()
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    console_handler.setFormatter(formatter)
    return logger
