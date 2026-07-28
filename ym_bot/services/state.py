import os
from typing import Dict, List


class StateManager:
    user_queries: Dict[int, str] = {}
    user_states: Dict[int, List] = {}
    user_message_ids: Dict[int, int] = {}
    user_track_data: Dict[int, Dict] = {}
    admin_waiting: Dict[int, str] = {}

    @classmethod
    def clear_user(cls, cid):
        cls.user_queries.pop(cid, None)
        cls.user_states.pop(cid, None)
        cls.user_message_ids.pop(cid, None)
        cls.admin_waiting.pop(cid, None)
        if cid in cls.user_track_data:
            fp = cls.user_track_data[cid].get('file_path')
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except:
                    pass
            cls.user_track_data.pop(cid, None)
