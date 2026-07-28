import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import requests
from yandex_music import Client

from ym_bot.config import Config, Patterns
from ym_bot.logger import logger
from ym_bot.models import PlaylistInfo


class YandexMusicAPI:
    client = None

    @classmethod
    def init(cls):
        try:
            cls.client = Client(Config.YM_TOKEN).init()
            logger.info("Yandex.Music client initialized")
        except Exception as e:
            logger.error(f"Failed to init YM client: {e}")
            cls.client = None

    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[<>:"/\\|?*]', '', name)[:100]

    @classmethod
    def get_track_filename(cls, track):
        arts = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
        return f"{cls.sanitize_filename(arts)} - {cls.sanitize_filename(track.title)}.mp3"

    @staticmethod
    def get_album_id(track):
        if hasattr(track, 'albums') and track.albums:
            return track.albums[0].id
        if hasattr(track, 'album') and track.album:
            return track.album.id
        return None

    @classmethod
    @lru_cache(maxsize=128)
    def get_track(cls, track_id, album_id=None):
        try:
            ts = f"{track_id}:{album_id}" if album_id else str(track_id)
            tl = cls.client.tracks(ts)
            return tl[0] if tl else None
        except:
            return None

    @classmethod
    @lru_cache(maxsize=128)
    def get_artist(cls, artist_id):
        try:
            al = cls.client.artists(artist_id)
            return al[0] if al else None
        except:
            return None

    @classmethod
    @lru_cache(maxsize=128)
    def get_album(cls, album_id):
        try:
            al = cls.client.albums(album_id)
            return al[0].with_tracks() if al else None
        except:
            return None

    @classmethod
    def parse_playlist_url(cls, url):
        m = Patterns.PLAYLIST_URL.search(url.split('?')[0])
        return PlaylistInfo(owner=m.group(1), playlist_id=m.group(2)) if m else None

    @classmethod
    def get_playlist(cls, pi):
        try:
            url = f"https://api.music.yandex.net/users/{pi.owner}/playlists/{pi.playlist_id}"
            headers = {'Authorization': f'OAuth {cls.client.token}', 'User-Agent': 'Yandex-Music-API', 'Accept': 'application/json'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            result = resp.json().get('result')
            if not result:
                return None
            td_list = [t.get('track') for t in result.get('tracks', [])[:Config.MAX_PLAYLIST_TRACKS] if t.get('track')]
            tracks = cls._fetch_track_batch(td_list)

            class SP:
                def __init__(s, title, owner_name, tl):
                    s.title, s._on, s._t = title, owner_name, tl

                @property
                def owner(s):
                    class O:
                        def __init__(ss, n):
                            ss.name = n
                    return O(s._on)

                @property
                def tracks(s):
                    return s._t

            return SP(result.get('title', 'Unknown'), result.get('owner', {}).get('name', 'Unknown'), tracks)
        except:
            return None

    @classmethod
    def _fetch_track_batch(cls, td_list):
        tracks = []

        def fetch(td):
            try:
                tid = td.get('id')
                if not tid:
                    return None
                albs = td.get('albums', [])
                return cls.get_track(tid, albs[0].get('id') if albs else None)
            except:
                return None

        with ThreadPoolExecutor(max_workers=10) as ex:
            for f in as_completed([ex.submit(fetch, td) for td in td_list]):
                t = f.result()
                if t:
                    tracks.append(t)
        return tracks

    @classmethod
    def search_playlists(cls, query):
        try:
            sr = cls.client.search(query, type_='playlist')
            return sr.playlists.results[:50] if sr and sr.playlists and sr.playlists.results else []
        except:
            return []

    @classmethod
    def search(cls, query, search_type):
        try:
            return cls.client.search(query, type_=search_type)
        except:
            return None
