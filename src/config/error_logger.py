import logging
import os
import json
from logging.handlers import RotatingFileHandler

# ✅ Ensure 'logs/' directory exists
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "errors.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ✅ Logger Configuration
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep 3 backup logs

logger = logging.getLogger("error_logger")
logger.setLevel(logging.ERROR)  # Log only ERROR and higher levels

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
file_handler.setLevel(logging.ERROR)  # Capture only ERROR and above

# ✅ Custom JSON Formatter
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

        if hasattr(record, "error"):
            log_record.update(record.error)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, indent=4)

formatter = JSONFormatter()
file_handler.setFormatter(formatter)

# ✅ Attach handler (ONLY file logging, no console prints)
logger.addHandler(file_handler)

# Prevent logs from being duplicated by parent loggers
logger.propagate = False
