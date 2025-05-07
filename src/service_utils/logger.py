import logging
import sys
import os
from typing import Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path
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

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_dir: Optional[str | Path] = None,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,  # Хранить 5 файлов
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Настройка логгера с поддержкой ротации файлов

    Args:
        name: Имя логгера
        level: Уровень логирования
        log_dir: Директория для файлов логов
        log_to_console: Выводить ли логи в консоль
        max_bytes: Максимальный размер файла до ротации (по умолчанию 10MB)
        backup_count: Количество файлов для хранения (по умолчанию 5)
        log_format: Формат сообщений лога (если None, используется формат по умолчанию)

    Returns:
        logging.Logger: Настроенный логгер
    """
    log_format = log_format or "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Очищаем существующие хендлеры

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter(log_format))
        logger.addHandler(console_handler)

    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Основной лог файл
        main_log = log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            filename=main_log,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)

        # Отдельный файл для ошибок
        error_log = log_dir / f"{name}.error.log"
        error_handler = RotatingFileHandler(
            filename=error_log,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(error_handler)

    return logger