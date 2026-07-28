import re


class Config:
    BATCH_SIZE = 50
    BATCH_WAIT = 15
    YM_TOKEN = ''
    BOT_TOKEN = ''
    VK_TOKEN = ''
    ADMIN_IDS = []
    CHANNEL_ID = -100
    CHANNEL_USERNAME = ''
    CHANNEL_LINK = 'https://t.me/'
    AD_CYCLE = 3
    PER_PAGE = 6
    MAX_INLINE_RESULTS = 10
    AUDIO_BITRATE = 192
    MAX_PLAYLIST_TRACKS = 1000
    DB_NAME = 'users.db'
    MEDIA_DIR = 'media'
    OUTPUT_DIR = 'downloads'
    UPDATE_ID_FILE = 'last_update_id.txt'
    MSG_MAX_AGE = 30

    @classmethod
    def bootstrap(cls):
        from ym_bot.settings import SettingsStore

        store = SettingsStore.load()
        store.apply_to_config()
        return store


class Patterns:
    TRACK_URL = re.compile(r'https://music\.yandex\.[a-z]{2,3}/album/(\d+)/track/(\d+)')
    ALBUM_URL = re.compile(r'https://music\.yandex\.[a-z]{2,3}/album/(\d+)(?:\?.*)?$')
    ARTIST_URL = re.compile(r'https://music\.yandex\.[a-z]{2,3}/artist/(\d+)')
    PLAYLIST_URL = re.compile(
        r'/users/(.*?)/playlists/(\d+)|/playlists/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})|/playlists/lk\.([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
    )
    INLINE_BUTTON = re.compile(r'\{inline url="([^"]+)"\}(.+?)(?=\{inline|$)', re.DOTALL)
