import logging
import sys
from .context import request_id_ctx_var

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = request_id_ctx_var.get() or 'no-request-id'
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name: str, level=logging.INFO):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Очищаем существующие хендлеры
    logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter(log_format))
    logger.addHandler(handler)

    return logger