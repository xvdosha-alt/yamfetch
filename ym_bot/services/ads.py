from ym_bot.config import Config
from ym_bot.emoji import Emoji
from ym_bot.persistence.database import Database
from ym_bot.ui.keyboards import KeyboardBuilder


class AdvertisementManager:
    @staticmethod
    def is_subscribed(bot, user_id):
        try:
            m = bot.get_chat_member(f"@{Config.CHANNEL_USERNAME}", user_id)
            return m.status in ['member', 'administrator', 'creator']
        except:
            return False

    @classmethod
    def maybe_send_ad(cls, bot, chat_id):
        if cls.is_subscribed(bot, chat_id):
            Database.reset_ad_counter(chat_id)
            return False
        counter = Database.increment_ad_counter(chat_id)
        if counter < Config.AD_CYCLE:
            return False
        ad_text = f'''{Emoji.AD} <b>Подпишитесь на наш канал!</b>

{Emoji.MUSIC} Новости и обновления бота
{Emoji.NOTES} Музыкальные подборки
{Emoji.STAR} Эксклюзивный контент'''
        bot.send_message(chat_id, ad_text, reply_markup=KeyboardBuilder.create_ad_keyboard(), parse_mode='HTML')
        return True
