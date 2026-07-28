from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import telebot


@dataclass
class BotContext:
    bot: telebot.TeleBot
    executor: ThreadPoolExecutor
    effect_executor: ThreadPoolExecutor
    boot_time: float
