"""
Logging Module
Centralized logging system
"""

import logging
import sys
from typing import Dict


class Logger:
    """Central logger"""
    
    def __init__(self, name: str = "airone"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def critical(self, msg: str):
        self.logger.critical(msg)


# Example
if __name__ == "__main__":
    logger = Logger()
    logger.info("System started")