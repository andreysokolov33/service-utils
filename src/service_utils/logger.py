import logging
import sys
import os
import re
from typing import Optional, Set, Pattern, Dict, Any
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .context import request_id_ctx_var

class SensitiveDataFilter(logging.Filter):
    """Фильтр для маскирования чувствительных данных в логах"""

    # Паттерны для поиска чувствительных данных
    PATTERNS: Dict[str, Pattern] = {
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        'phone': re.compile(r'(\+7|8)[- _]*\d{3}[- _]*\d{3}[- _]*\d{2}[- _]*\d{2}'),
        'password': re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
        'token': re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
        'secret': re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
    }

    # Ключи, которые нужно маскировать в словарях
    SENSITIVE_KEYS: Set[str] = {
        'password', 'token', 'secret', 'api_key', 'access_token',
        'refresh_token', 'private_key', 'email', 'phone'
    }

    def __init__(self):
        super().__init__()
        self.replacement = '***'

    def _mask_sensitive_data(self, text: str) -> str:
        """Маскирует чувствительные данные в тексте"""
        for pattern in self.PATTERNS.values():
            text = pattern.sub(self.replacement, text)
        return text

    def _mask_dict_values(self, obj: Any) -> Any:
        """Рекурсивно маскирует чувствительные данные в словарях"""
        if isinstance(obj, dict):
            return {
                k: self.replacement if k.lower() in self.SENSITIVE_KEYS else self._mask_dict_values(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._mask_dict_values(item) for item in obj]
        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, (dict, list)):
            record.msg = self._mask_dict_values(record.msg)
        elif isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)

        if record.args:
            record.args = tuple(
                self._mask_dict_values(arg) if isinstance(arg, (dict, list)) else
                self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True

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
    Настройка логгера с поддержкой ротации файлов и фильтрацией чувствительных данных

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
    log_format = log_format or (
        "%(asctime)s - %(levelname)s - [%(request_id)s] - "
        "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Очищаем существующие хендлеры

    # Добавляем фильтр чувствительных данных
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)

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