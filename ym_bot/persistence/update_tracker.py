import os
import threading

from ym_bot.config import Config
from ym_bot.logger import logger


class UpdateTracker:
    _file = Config.UPDATE_ID_FILE
    _last_id = 0
    _lock = threading.Lock()

    @classmethod
    def load(cls):
        try:
            if os.path.exists(cls._file):
                with open(cls._file, 'r') as f:
                    cls._last_id = int(f.read().strip())
                    logger.info(f"Loaded last_update_id: {cls._last_id}")
        except:
            cls._last_id = 0

    @classmethod
    def save(cls, update_id: int):
        with cls._lock:
            if update_id > cls._last_id:
                cls._last_id = update_id
                try:
                    with open(cls._file, 'w') as f:
                        f.write(str(update_id))
                except:
                    pass

    @classmethod
    def is_processed(cls, update_id: int) -> bool:
        return update_id <= cls._last_id

    @classmethod
    def get_last(cls) -> int:
        return cls._last_id
