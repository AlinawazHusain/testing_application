import logging
import os
import json
from logging.handlers import RotatingFileHandler

# Directory and file setup
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "API_hit.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep 3 backup logs

# Logger Configuration
logger = logging.getLogger("info_logger")
logger.setLevel(logging.INFO)  # Only log INFO level

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
file_handler.setLevel(logging.INFO)

# Custom JSON Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "module": record.name,
            "file": record.pathname,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage().replace("\n", " ")
        }

        if hasattr(record, "info") and isinstance(record.info, dict):
            log_record.update(record.info) 

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, indent=4)

# Apply formatter
formatter = JSONFormatter()
file_handler.setFormatter(formatter)

# Attach handlers
logger.addHandler(file_handler)

# Ensure only INFO logs are captured
logger.propagate = False
