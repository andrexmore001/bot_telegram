import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """
    Formateador de logs personalizado con colores para consola.
    """
    
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # Formato: [TIMESTAMP] [LEVEL] [LOGGER] - MESSAGE
    format_str = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: reset + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str):
    """
    Retorna un logger configurado con salida a consola (colores) y archivo (plano).
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 1. Handler para Consola (Stdout con colores)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        # 2. Handler para Archivo (Plano, sin colores para mejor lectura en editores)
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "bot.log"),
            maxBytes=5*1024*1024,  # 5MB antes de rotar
            backupCount=3,         # Mantener hasta 3 archivos viejos
            encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Evitar duplicados si se propaga al root logger
        logger.propagate = False
        
    return logger

# Logger global para la aplicación
logger = get_logger("BOT_INTERRAPIDISIMO")
