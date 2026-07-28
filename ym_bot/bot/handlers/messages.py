from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.audio.tags import TagManager
from ym_bot.config import Config, Patterns
from ym_bot.emoji import Emoji
from ym_bot.persistence.database import Database
from ym_bot.services.state import StateManager
from ym_bot.ui.keyboards import KeyboardBuilder


class MessageHandler:
    def __init__(self, ctx, downloads):
        self.ctx = ctx
        self.downloads = downloads

    def handle_message(self, message):
        cid, text = message.chat.id, message.text
        if not text or text.startswith('/') or message.reply_to_message is not None:
            return
        uname, fname = message.from_user.username, message.from_user.first_name
        Database.add_user(cid, uname, fname)
        if cid in StateManager.admin_waiting:
            wt = StateManager.admin_waiting.pop(cid)
            if wt == 'user_info':
                try:
                    tid = int(text.strip())
                    us = Database.get_user_stats(tid)
                    if us:
                        st = f'👤 <b>Пользователь {tid}</b>\n\n📛 @{us.get("username") or "N/A"}\n📝 {us.get("first_name") or "N/A"}\n📅 {us.get("added_date", "N/A")}\n⚙️ {"Выбор" if us.get("has_edit",1)==1 else "Быстрый"}\n\n📊 <b>Статистика:</b>\n⬇️ {us.get("downloads",0)} | 🔍 {us.get("searches",0)} | 🎛 {us.get("effects",0)}\n✏️ {us.get("edits",0)} | 📀 {us.get("album_downloads",0)} | ▶️ {us.get("playlist_downloads",0)}\n🏆 Макс: {us.get("max_batch_size",0)} тр.'
                    else:
                        st = f"❌ Пользователь {tid} не найден"
                    kb = InlineKeyboardMarkup()
                    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
                    self.ctx.bot.send_message(cid, st, reply_markup=kb, parse_mode='HTML')
                except ValueError:
                    self.ctx.bot.send_message(cid, "❌ Введите числовой ID", parse_mode='HTML')
                return
        if cid in StateManager.user_track_data and StateManager.user_track_data[cid].get('waiting_for'):
            wf = StateManager.user_track_data[cid]['waiting_for']
            fp = StateManager.user_track_data[cid]['file_path']
            if wf == 'title' and TagManager.set_tags(fp, title=text):
                StateManager.user_track_data[cid]['title'] = text
                StateManager.user_track_data[cid]['waiting_for'] = None
                Database.log_action(cid, 'edit_tag', details=f'title_to={text}', track_title=text, artist_name=StateManager.user_track_data[cid].get('artist'))
                self.ctx.bot.send_message(cid, f'{Emoji.MUSIC} <b>Редактирование</b>\n\n{Emoji.NOTE} Название: <b>{text}</b>\n{Emoji.SUCCESS} Обновлено!', reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
                return
            elif wf == 'artist' and TagManager.set_tags(fp, artist=text):
                StateManager.user_track_data[cid]['artist'] = text
                StateManager.user_track_data[cid]['waiting_for'] = None
                Database.log_action(cid, 'edit_tag', details=f'artist_to={text}', track_title=StateManager.user_track_data[cid].get('title'), artist_name=text)
                self.ctx.bot.send_message(cid, f'{Emoji.MUSIC} <b>Редактирование</b>\n\n{Emoji.USER} Автор: <b>{text}</b>\n{Emoji.SUCCESS} Обновлено!', reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
                return
        try:
            if cid not in Config.ADMIN_IDS:
                self.ctx.bot.delete_message(cid, message.message_id)
        except:
            pass
        tm = Patterns.TRACK_URL.match(text)
        if tm:
            aid, tid = tm.groups()
            track = YandexMusicAPI.get_track(tid, aid)
            if track:
                if Database.get_has_edit(cid) == 1:
                    perf = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
                    self.ctx.bot.send_message(cid, f'{Emoji.MUSIC} <b>{track.title}</b>\n{Emoji.USER} {perf}', reply_markup=KeyboardBuilder.create_single_track_keyboard(tid, aid), parse_mode='HTML')
                else:
                    self.ctx.bot.send_message(cid, f'{Emoji.LOADING} <b>Скачиваю...</b>', parse_mode='HTML')
                    self.ctx.executor.submit(self.downloads.download_and_send_track, cid, track)
            else:
                self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Трек не найден</b>', parse_mode='HTML')
            return
        am = Patterns.ALBUM_URL.match(text)
        if am:
            aid = am.group(1)
            album = YandexMusicAPI.get_album(aid)
            if album:
                tracks = album.volumes[0] if album.volumes else (album.tracks if album.tracks else [])
                art = ', '.join(a.name for a in album.artists) if album.artists else 'Unknown'
                label = f'{Emoji.ALBUM} <b>{album.title}</b>\n{Emoji.USER} {art}\n{Emoji.MUSIC} {len(tracks)} треков'
                StateManager.user_states[cid] = [{'type': 'tracks', 'tracks': tracks, 'album_id': aid, 'page': 0, 'label': label}]
                self.ctx.bot.send_message(cid, label, reply_markup=KeyboardBuilder.create_paginated_download_keyboard(tracks, 0, aid), parse_mode='HTML')
            return
        pi = YandexMusicAPI.parse_playlist_url(text)
        if pi:
            wm = self.ctx.bot.send_message(cid, f"{Emoji.LOADING} <b>Загрузка плейлиста...</b>", parse_mode='HTML')

            def pt():
                pl = YandexMusicAPI.get_playlist(pi)
                self.ctx.bot.delete_message(cid, wm.message_id)
                if pl and pl.tracks:
                    label = f'{Emoji.MUSIC} <b>{pl.title}</b>\n{Emoji.USER} {pl.owner.name}\n{Emoji.NOTES} {len(pl.tracks)} треков'
                    StateManager.user_states[cid] = [{'type': 'tracks', 'tracks': pl.tracks, 'playlist_info': pi, 'page': 0, 'label': label}]
                    self.ctx.bot.send_message(cid, label, reply_markup=KeyboardBuilder.create_paginated_download_keyboard(pl.tracks, 0, playlist_info=pi), parse_mode='HTML')

            self.ctx.executor.submit(pt)
            return
        arm = Patterns.ARTIST_URL.match(text)
        if arm:
            arid = arm.group(1)
            artist = YandexMusicAPI.get_artist(arid)
            if artist:
                albs = artist.get_albums()
                label = f'{Emoji.USER} <b>{artist.name}</b>\n{Emoji.ALBUM} {len(albs)} альбомов'
                StateManager.user_states[cid] = [{'type': 'artist_albums', 'items': albs, 'page': 0, 'label': label}]
                self.ctx.bot.send_message(cid, label, reply_markup=KeyboardBuilder.create_paginated_keyboard(albs, 'album', 0, get_text=lambda i: f"{i.title} ({getattr(i, 'year', '?')})"), parse_mode='HTML')
            return
        Database.log_action(cid, 'search', details=text)
        StateManager.user_queries[cid] = text
        self.ctx.bot.send_message(cid, f'{Emoji.SEARCH} <b>Поиск:</b> <i>{text}</i>\n\n{Emoji.ARROW} Выберите тип:', reply_markup=KeyboardBuilder.create_search_type_keyboard(), parse_mode='HTML')
