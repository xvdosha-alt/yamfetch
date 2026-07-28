import multiprocessing as mp
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import telebot

from ym_bot.bot.context import BotContext
from ym_bot.bot.downloads import DownloadService
from ym_bot.bot.handlers.callbacks import CallbackHandler
from ym_bot.bot.handlers.commands import CommandHandler
from ym_bot.bot.handlers.inline import InlineHandler
from ym_bot.bot.handlers.messages import MessageHandler
from ym_bot.bot.navigation import ListNavigationService
from ym_bot.bot.presenters import AdminPresenter
from ym_bot.config import Config
from ym_bot.logger import logger
from ym_bot.persistence.update_tracker import UpdateTracker


class MusicBot:
    def __init__(self):
        self.bot = telebot.TeleBot(Config.BOT_TOKEN, threaded=True, num_threads=8)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.effect_executor = ThreadPoolExecutor(max_workers=mp.cpu_count())
        self.ctx = BotContext(
            bot=self.bot,
            executor=self.executor,
            effect_executor=self.effect_executor,
            boot_time=time.time(),
        )
        self.downloads = DownloadService(self.ctx)
        self.presenter = AdminPresenter()
        self.navigation = ListNavigationService(self.ctx)
        self.commands = CommandHandler(self.ctx, self.downloads)
        self.messages = MessageHandler(self.ctx, self.downloads)
        self.inline = InlineHandler(self.ctx)
        self.callbacks = CallbackHandler(self.ctx, self.downloads, self.presenter, self.navigation, self.commands)
        self._setup_handlers()

    def _setup_handlers(self):
        self.bot.message_handler(commands=['start'])(self.commands.handle_start)
        self.bot.message_handler(commands=['help'])(self.commands.handle_help)
        self.bot.message_handler(commands=['has_edit'])(self.commands.handle_has_edit)
        self.bot.message_handler(commands=['stats'])(self.commands.handle_stats)
        self.bot.message_handler(commands=['admin'])(self.commands.handle_admin)
        self.bot.message_handler(commands=['spam'])(self.commands.handle_spam)
        self.bot.message_handler(commands=['debug'])(self.commands.handle_debug)
        self.bot.message_handler(commands=['clear'])(self.commands.handle_clear)
        self.bot.message_handler(commands=['d'])(self.commands.handle_d_command)
        self.bot.message_handler(content_types=['photo'])(self.commands.handle_photo)
        self.bot.message_handler(func=lambda m: True)(self.messages.handle_message)
        self.bot.callback_query_handler(func=lambda c: True)(self.callbacks.handle_callback)
        self.bot.inline_handler(lambda q: True)(self.inline.handle_inline)
        self.bot.chosen_inline_handler(func=lambda c: True)(self.inline.handle_chosen_inline)

    def run(self):
        logger.info("Bot starting...")
        UpdateTracker.load()
        print(f"🚀 Бот запущен! boot_time={datetime.fromtimestamp(self.ctx.boot_time).strftime('%H:%M:%S')}")
        try:
            self.bot.remove_webhook()
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.error(traceback.format_exc())
