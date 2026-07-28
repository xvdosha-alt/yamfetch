import os
from pathlib import Path
from typing import List

from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.config import Config, Patterns
from ym_bot.logger import logger
from ym_bot.models import PlaylistInfo


class LocalDownloadService:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or Config.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def track_path(self, track, folder=None):
        base = Path(folder) if folder else self.output_dir
        base.mkdir(parents=True, exist_ok=True)
        return base / YandexMusicAPI.get_track_filename(track)

    def download_track(self, track, folder=None) -> Path:
        path = self.track_path(track, folder)
        track.download(str(path), codec='mp3', bitrate_in_kbps=Config.AUDIO_BITRATE)
        logger.info(f'Saved: {path}')
        return path

    def album_tracks(self, album):
        if hasattr(album, 'volumes') and album.volumes:
            return [track for volume in album.volumes for track in volume]
        if hasattr(album, 'tracks') and album.tracks:
            return list(album.tracks)
        return []

    def download_album(self, album_id, folder=None) -> List[Path]:
        album = YandexMusicAPI.get_album(album_id)
        if not album:
            raise RuntimeError(f'Альбом {album_id} не найден')
        target = Path(folder) if folder else self.output_dir / YandexMusicAPI.sanitize_filename(album.title)
        saved = []
        for stub in self.album_tracks(album):
            track = YandexMusicAPI.get_track(stub.id, album_id)
            if track:
                saved.append(self.download_track(track, target))
        return saved

    def download_playlist(self, playlist_info: PlaylistInfo, folder=None) -> List[Path]:
        playlist = YandexMusicAPI.get_playlist(playlist_info)
        if not playlist or not playlist.tracks:
            raise RuntimeError('Плейлист не найден или пуст')
        target = Path(folder) if folder else self.output_dir / YandexMusicAPI.sanitize_filename(playlist.title)
        return [self.download_track(track, target) for track in playlist.tracks if track]

    def download_url(self, url: str, folder=None) -> List[Path]:
        text = url.strip()
        track_match = Patterns.TRACK_URL.match(text)
        if track_match:
            album_id, track_id = track_match.groups()
            track = YandexMusicAPI.get_track(track_id, album_id)
            if not track:
                raise RuntimeError('Трек не найден')
            return [self.download_track(track, folder)]
        album_match = Patterns.ALBUM_URL.match(text)
        if album_match:
            return self.download_album(album_match.group(1), folder)
        playlist_info = YandexMusicAPI.parse_playlist_url(text)
        if playlist_info:
            return self.download_playlist(playlist_info, folder)
        raise RuntimeError('Не удалось распознать ссылку Яндекс.Музыки')

    def search_tracks(self, query: str, limit=10):
        result = YandexMusicAPI.search(query, 'track')
        if not result or not result.tracks or not result.tracks.results:
            return []
        return result.tracks.results[:limit]

    def download_query(self, query: str, folder=None, index=0) -> Path:
        tracks = self.search_tracks(query, limit=max(index + 1, 10))
        if not tracks:
            raise RuntimeError(f'Ничего не найдено: {query}')
        if index >= len(tracks):
            raise RuntimeError(f'В выдаче только {len(tracks)} треков, индекс {index} недоступен')
        track = tracks[index]
        album_id = YandexMusicAPI.get_album_id(track)
        full = YandexMusicAPI.get_track(track.id, album_id)
        if not full:
            raise RuntimeError('Не удалось загрузить метаданные трека')
        return self.download_track(full, folder)

    @staticmethod
    def format_track_line(index, track):
        artists = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
        return f'{index + 1}. {artists} — {track.title}'

    def print_search(self, query: str, limit=10):
        tracks = self.search_tracks(query, limit=limit)
        if not tracks:
            print('Ничего не найдено')
            return tracks
        for i, track in enumerate(tracks):
            print(self.format_track_line(i, track))
        return tracks
