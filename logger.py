#!/usr/bin/env python3
"""
logger.py - Sistema de logging unificado para checkpatch

Proporciona logging con niveles configurables y soporte para archivo de log.
"""

import logging
import sys
from pathlib import Path


# Colores ANSI para la consola
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


# Mapeo de niveles a prefijos y colores
LEVEL_CONFIG = {
    logging.DEBUG: ("DEBUG", Colors.GRAY),
    logging.INFO: ("INFO", Colors.CYAN),
    logging.WARNING: ("WARNING", Colors.YELLOW),
    logging.ERROR: ("ERROR", Colors.RED),
    logging.CRITICAL: ("CRITICAL", Colors.MAGENTA),
}


class ColoredFormatter(logging.Formatter):
    """Formateador que añade colores a los mensajes de consola."""
    
    def __init__(self, use_colors=True):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record):
        if self.use_colors:
            level_name, color = LEVEL_CONFIG.get(record.levelno, ("INFO", Colors.CYAN))
            
            # Si el mensaje tiene un prefijo como [ANALYZER], [AUTOFIX], etc., respetarlo
            msg = record.getMessage()
            if msg.startswith('['):
                # Mantener el formato existente con prefijo
                return f"{color}{msg}{Colors.RESET}"
            else:
                # Nuevo formato con nivel de log
                return f"{color}[{level_name}]{Colors.RESET} {msg}"
        else:
            return record.getMessage()


class CheckpatchLogger:
    """Logger singleton para toda la aplicación."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('checkpatch')
            self.logger.setLevel(logging.DEBUG)  # Capturar todos los niveles
            self.logger.propagate = False
            self._initialized = True
            self.file_handler = None
            self.console_handler = None
    
    def setup(self, level=logging.INFO, log_file=None, use_colors=True):
        """
        Configura el sistema de logging.
        
        Args:
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path opcional para archivo de log
            use_colors: Si True, usa colores en la salida de consola
        """
        # Limpiar handlers existentes
        self.logger.handlers.clear()
        
        # Console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(level)
        self.console_handler.setFormatter(ColoredFormatter(use_colors=use_colors))
        self.logger.addHandler(self.console_handler)
        
        # File handler (opcional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
            self.file_handler.setLevel(logging.DEBUG)  # El archivo captura todo
            # Sin colores para el archivo
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.file_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.file_handler)
    
    def debug(self, msg):
        """Log a nivel DEBUG."""
        self.logger.debug(msg)
    
    def info(self, msg):
        """Log a nivel INFO."""
        self.logger.info(msg)
    
    def warning(self, msg):
        """Log a nivel WARNING."""
        self.logger.warning(msg)
    
    def error(self, msg):
        """Log a nivel ERROR."""
        self.logger.error(msg)
    
    def critical(self, msg):
        """Log a nivel CRITICAL."""
        self.logger.critical(msg)


# Instancia global singleton
_logger_instance = CheckpatchLogger()


def setup_logging(level=logging.INFO, log_file=None, use_colors=True):
    """
    Configura el sistema de logging global.
    
    Args:
        level: Nivel de logging (logging.DEBUG, logging.INFO, etc.)
        log_file: Path opcional para archivo de log
        use_colors: Si True, usa colores en la salida de consola
    """
    _logger_instance.setup(level, log_file, use_colors)


def debug(msg):
    """Log a nivel DEBUG."""
    _logger_instance.debug(msg)


def info(msg):
    """Log a nivel INFO."""
    _logger_instance.info(msg)


def warning(msg):
    """Log a nivel WARNING."""
    _logger_instance.warning(msg)


def error(msg):
    """Log a nivel ERROR."""
    _logger_instance.error(msg)


def critical(msg):
    """Log a nivel CRITICAL."""
    _logger_instance.critical(msg)


def get_level_from_string(level_str):
    """
    Convierte string a nivel de logging.
    
    Args:
        level_str: String con el nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging level constant
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.INFO)
