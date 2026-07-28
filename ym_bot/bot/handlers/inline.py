from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent

from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.config import Config, Patterns
from ym_bot.emoji import Emoji
from ym_bot.persistence.database import Database


class InlineHandler:
    def __init__(self, ctx):
        self.ctx = ctx

    def handle_inline(self, iq):
        Database.add_user(iq.from_user.id, iq.from_user.username, iq.from_user.first_name)
        qt = iq.query.strip()
        if not qt:
            return
        Database.log_action(iq.from_user.id, 'inline_search', details=qt)
        tm = Patterns.TRACK_URL.match(qt)
        if tm:
            aid, tid = tm.groups()
            track = YandexMusicAPI.get_track(tid, aid)
            if track:
                title = track.title
                arts = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
                tt = f'{Emoji.MUSIC} <b>{title}</b>\n{Emoji.USER} {arts}\n\n{Emoji.DOWNLOAD} Нажмите'
                bi = self.ctx.bot.get_me()
                mk = InlineKeyboardMarkup()
                mk.add(InlineKeyboardButton("📥 Скачать", url=f"https://t.me/{bi.username}?start=download_{tid}_{aid}"))
                self.ctx.bot.answer_inline_query(iq.id, [InlineQueryResultArticle(id="0", title=f"🎵 {title}", description=arts, input_message_content=InputTextMessageContent(tt, parse_mode='HTML'), reply_markup=mk)], cache_time=1)
                return
        try:
            sr = YandexMusicAPI.search(qt, 'track')
            results = []
            if sr and sr.tracks and sr.tracks.results:
                bi = self.ctx.bot.get_me()
                for i, track in enumerate(sr.tracks.results[:Config.MAX_INLINE_RESULTS]):
                    title = track.title
                    arts = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
                    tt = f'{Emoji.MUSIC} <b>{title}</b>\n{Emoji.USER} {arts}\n\n{Emoji.DOWNLOAD} Нажмите'
                    aid = YandexMusicAPI.get_album_id(track)
                    sp = f"download_{track.id}_{aid}" if aid else f"download_{track.id}"
                    mk = InlineKeyboardMarkup()
                    mk.add(InlineKeyboardButton("📥 Скачать", url=f"https://t.me/{bi.username}?start={sp}", icon_custom_emoji_id="5899757765743615694"))
                    results.append(InlineQueryResultArticle(id=str(i), title=f"🎵 {title}", description=arts, input_message_content=InputTextMessageContent(tt, parse_mode='HTML'), reply_markup=mk))
            self.ctx.bot.answer_inline_query(iq.id, results, cache_time=1)
        except:
            self.ctx.bot.answer_inline_query(iq.id, [], cache_time=1)

    def handle_chosen_inline(self, chosen):
        try:
            rid, imid, query = chosen.result_id, chosen.inline_message_id, chosen.query
            if not imid or not query:
                return
            Database.log_action(chosen.from_user.id, 'inline_chosen', details=f'result={rid} query={query}')
            sr = YandexMusicAPI.search(query, 'track')
            if not (sr and sr.tracks and sr.tracks.results):
                return
            tracks = sr.tracks.results[:Config.MAX_INLINE_RESULTS]
            try:
                idx = int(rid)
                if idx >= len(tracks):
                    return
                track = tracks[idx]
            except:
                return
            title = track.title
            arts = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
            tt = f'{Emoji.MUSIC} <b>{title}</b>\n{Emoji.USER} {arts}\n\n{Emoji.DOWNLOAD} Нажмите'
            bi = self.ctx.bot.get_me()
            aid = YandexMusicAPI.get_album_id(track)
            sp = f"download_{track.id}_{aid}" if aid else f"download_{track.id}"
            mk = InlineKeyboardMarkup()
            mk.add(InlineKeyboardButton("📥 Скачать", url=f"https://t.me/{bi.username}?start={sp}", icon_custom_emoji_id="5899757765743615694"))
            try:
                self.ctx.bot.edit_message_text(inline_message_id=imid, text=tt, parse_mode='HTML', reply_markup=mk)
            except:
                pass
        except:
            pass
