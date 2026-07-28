import asyncio
import os

from ym_bot.api.vk import VKMusicAPI
from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.bot.music_bot import MusicBot
from ym_bot.config import Config
from ym_bot.persistence.database import Database


class Application:
    @staticmethod
    def bootstrap():
        Config.bootstrap()
        os.makedirs(Config.MEDIA_DIR, exist_ok=True)
        Database.init()
        YandexMusicAPI.init()
        if Config.VK_TOKEN:
            asyncio.run(VKMusicAPI.auth())

    @staticmethod
    def run():
        Application.bootstrap()
        MusicBot().run()
