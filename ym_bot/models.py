from dataclasses import dataclass


@dataclass
class PlaylistInfo:
    owner: str
    playlist_id: str
