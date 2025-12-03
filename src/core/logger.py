import logging
import sys, os
import queue
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from configs.config import LOG_FILE





class Logger:
    _instance = None

    def __new__(cls, log_file=LOG_FILE, max_bytes=5*1024*1024, backup_count=3, console=False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger(log_file, max_bytes, backup_count, console)
        return cls._instance

    def _init_logger(self, log_file, max_bytes, backup_count, console):
        self.log_queue = queue.Queue(-1)
        self.logger = logging.getLogger("AsyncLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Handlers
        handlers = []

        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)

        # Queue-based async logging
        queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
        self.listener = QueueListener(self.log_queue, *handlers, respect_handler_level=True)
        self.listener.start()

        # Catch unhandled exceptions
        sys.excepthook = self._handle_exception

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    def get_logger(self):
        return self.logger

    def stop(self):
        self.listener.stop()



logger = Logger(console=True).get_logger()