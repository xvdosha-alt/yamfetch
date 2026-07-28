from ym_bot.config import Config
from ym_bot.logger import logger


class VKMusicAPI:
    service = None
    USER_AGENT = 'KateMobileAndroid/56 lite (Android 5.0; SDK 21; armeabi-v7a; Sony D2303; ru)'

    @classmethod
    def token(cls):
        return Config.VK_TOKEN

    @classmethod
    async def auth(cls):
        try:
            from vkpymusic import Service

            if not cls.token():
                return False
            cls.service = Service(cls.USER_AGENT, cls.token())
            if await cls.service.is_token_valid_async():
                logger.info("VK API: Auth successful")
                return True
            logger.error("VK API: Token invalid")
            return False
        except Exception as e:
            logger.error(f"VK API: Init error: {e}")
            return False

    @classmethod
    async def search_uncensored(cls, query):
        if not cls.service and not await cls.auth():
            return []
        try:
            r = await cls.service.search_songs_by_text_async(query, count=5)
            return r if r else []
        except:
            return []

    @classmethod
    async def get_song_by_id(cls, owner_id, track_id):
        if not cls.service:
            await cls.auth()
        try:
            songs = await cls.service.get_songs_by_id_async([f"{owner_id}_{track_id}"])
            return songs[0] if songs else None
        except:
            return None
