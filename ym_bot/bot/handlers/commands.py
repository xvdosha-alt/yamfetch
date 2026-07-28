import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.audio.tags import TagManager
from ym_bot.config import Config, Patterns
from ym_bot.emoji import Emoji
from ym_bot.logger import logger
from ym_bot.persistence.database import Database
from ym_bot.services.state import StateManager
from ym_bot.ui.keyboards import KeyboardBuilder


class CommandHandler:
    def __init__(self, ctx, downloads):
        self.ctx = ctx
        self.downloads = downloads

    def handle_start(self, message):
        cid, uname, fname = message.chat.id, message.from_user.username, message.from_user.first_name
        Database.add_user(cid, uname, fname)
        Database.log_action(cid, 'start', details=message.text)
        payload = message.text.split(' ', 1)[1] if ' ' in message.text else None
        if payload and payload.startswith('user_'):
            try:
                ts = int(payload.split('_')[1])
                ud = Database.get_user_by_timestamp(ts)
                if ud:
                    if ud['user_id'] == cid:
                        text = f'{Emoji.HELLO}<b> Это вы!</b> {Emoji.STAR}\n\n📅 <b>Дата:</b> <code>{ud["added_date"]}</code>\n⚙️ <b>Режим:</b> {"Выбор" if ud["has_edit"]==1 else "Быстрый"}'
                    else:
                        text = f'{Emoji.CANCEL} <b>Это не вы</b>'
                else:
                    text = f'{Emoji.CANCEL} <b>Не найден</b>\n\n⏱ <code>{ts}</code>\n📅 <code>{datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")}</code>'
                self.ctx.bot.send_message(cid, text, parse_mode='HTML')
            except Exception as e:
                self.ctx.bot.send_message(cid, f"{Emoji.CANCEL} <b>Ошибка:</b> {e}", parse_mode='HTML')
            return
        if payload and payload.startswith('download_'):
            parts = payload.split('_')
            if len(parts) >= 2:
                tid, aid = parts[1], parts[2] if len(parts) > 2 else None
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
        wt = f'{Emoji.HELLO}<b> Привет! </b>{Emoji.STAR}\n\n{Emoji.HEADPHONES} Я бот для скачивания музыки из <b>Яндекс.Музыки</b> {Emoji.NOTES}{Emoji.ROCKET}\n\n{Emoji.NOTE}<b> Отправь мне:</b>\n<blockquote>{Emoji.SEARCH} Название трека/альбома/артиста/плейлиста {Emoji.MIC}\n{Emoji.LINK} Ссылку на трек/альбом/плейлист/артиста {Emoji.DOWNLOAD}</blockquote>\n\n{Emoji.BULB} /help - подробная инструкция {Emoji.BOOK}{Emoji.QUESTION}'
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Загрузить в Яндекс.Музыку", url="https://t.me/YM_upload_bot", icon_custom_emoji_id="5899757765743615694"))
        kb.add(InlineKeyboardButton("Помощь", callback_data="show_help", icon_custom_emoji_id="5388953246486269495"))
        self.ctx.bot.send_message(cid, wt, reply_markup=kb, parse_mode='HTML')

    def handle_help(self, message):
        Database.add_user(message.chat.id, message.from_user.username, message.from_user.first_name)
        self._send_help_message(message.chat.id)

    def _send_help_message(self, cid, emid=None):
        ht = f'{Emoji.BOOK}<b> Инструкция </b>{Emoji.STAR}\n\n{Emoji.SEARCH}<b> Поиск:</b> Отправь название {Emoji.MAGNIFIER}\n{Emoji.LINK}<b> Ссылки:</b> Трек/Альбом/Плейлист {Emoji.NOTES}\n{Emoji.TRACK}<b> Плейлисты:</b> Ограничение 1000 треков {Emoji.HEADPHONES}\n{Emoji.ROCKET}<b> Инлайн:</b> @YM_get_bot запрос {Emoji.ROCKET}\n{Emoji.EFFECTS}<b> Эффекты:</b> Slow, Speed, Bass, Reverb {Emoji.MIXER}\n{Emoji.DISK}<b> Качество:</b> 192 kbps MP3\n{Emoji.GEAR}<b> Настройки:</b> /has_edit - переключить режим'
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Загрузить", url="https://t.me/YM_upload_bot", icon_custom_emoji_id="5899757765743615694"))
        kb.add(InlineKeyboardButton("Главная", callback_data="main_menu", icon_custom_emoji_id="5388953246486269495"))
        if emid:
            self.ctx.bot.edit_message_text(ht, cid, emid, reply_markup=kb, parse_mode='HTML')
        else:
            self.ctx.bot.send_message(cid, ht, reply_markup=kb, parse_mode='HTML')

    def handle_has_edit(self, message):
        cid = message.chat.id
        Database.add_user(cid, message.from_user.username, message.from_user.first_name)
        StateManager.user_states.pop(cid, None)
        nv = Database.toggle_has_edit(cid)
        Database.log_action(cid, 'toggle_edit', details=f'new_value={nv}')
        self.ctx.bot.send_message(cid, f'{Emoji.SUCCESS} <b>{"Режим выбора включен" if nv==1 else "Режим быстрого скачивания включен"}</b>', parse_mode='HTML')

    def handle_stats(self, message):
        Database.add_user(message.chat.id, message.from_user.username, message.from_user.first_name)
        if message.from_user.id in Config.ADMIN_IDS:
            self.ctx.bot.send_message(message.chat.id, f"📊 <b>Статистика</b>\n\n👥 Пользователей: <b>{Database.get_user_count()}</b>", parse_mode='HTML')
        else:
            self.ctx.bot.send_message(message.chat.id, "❌ <b>Нет доступа</b>", parse_mode='HTML')

    def handle_admin(self, message):
        cid = message.chat.id
        if message.from_user.id not in Config.ADMIN_IDS:
            self.ctx.bot.send_message(cid, "❌ <b>Нет доступа</b>", parse_mode='HTML')
            return
        Database.update_daily_unique_users()
        self.ctx.bot.send_message(cid, f"{Emoji.CROWN} <b>Админ-панель</b>\n\nВыберите раздел:", reply_markup=KeyboardBuilder.create_admin_panel_keyboard(), parse_mode='HTML')

    def handle_spam(self, message):
        if message.from_user.id not in Config.ADMIN_IDS:
            self.ctx.bot.send_message(message.chat.id, "❌ <b>Нет доступа</b>", parse_mode='HTML')
            return
        if not message.reply_to_message:
            self.ctx.bot.send_message(message.chat.id, "❌ <b>Ответьте на сообщение</b>", parse_mode='HTML')
            return
        reply = message.reply_to_message
        users = Database.get_all_users()
        if not users:
            self.ctx.bot.send_message(message.chat.id, "❌ <b>Нет пользователей</b>", parse_mode='HTML')
            return
        text = reply.text or reply.caption or ""
        entities = reply.entities or reply.caption_entities or []
        matches = Patterns.INLINE_BUTTON.findall(text)
        inline_buttons = [{'text': bt.strip(), 'url': url.strip()} for url, bt in matches]
        clean_text = Patterns.INLINE_BUTTON.sub('', text).strip()
        keyboard = None
        if inline_buttons:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for btn in inline_buttons:
                keyboard.add(InlineKeyboardButton(btn['text'], url=btn['url']))
        success, failed = 0, 0
        status_msg = self.ctx.bot.send_message(message.chat.id, "⏳ <b>Рассылка...</b>", parse_mode='HTML')

        def send_to(uid):
            nonlocal success, failed
            try:
                if reply.photo:
                    if clean_text:
                        self.ctx.bot.send_photo(uid, reply.photo[-1].file_id, caption=clean_text, caption_entities=entities if not inline_buttons else None, reply_markup=keyboard, parse_mode='HTML' if inline_buttons else None)
                    else:
                        self.ctx.bot.send_photo(uid, reply.photo[-1].file_id, reply_markup=keyboard)
                elif reply.video:
                    if clean_text:
                        self.ctx.bot.send_video(uid, reply.video.file_id, caption=clean_text, caption_entities=entities if not inline_buttons else None, reply_markup=keyboard, parse_mode='HTML' if inline_buttons else None)
                    else:
                        self.ctx.bot.send_video(uid, reply.video.file_id, reply_markup=keyboard)
                elif reply.audio:
                    if clean_text:
                        self.ctx.bot.send_audio(uid, reply.audio.file_id, caption=clean_text, caption_entities=entities if not inline_buttons else None, reply_markup=keyboard, parse_mode='HTML' if inline_buttons else None)
                    else:
                        self.ctx.bot.send_audio(uid, reply.audio.file_id, reply_markup=keyboard)
                elif reply.document:
                    if clean_text:
                        self.ctx.bot.send_document(uid, reply.document.file_id, caption=clean_text, caption_entities=entities if not inline_buttons else None, reply_markup=keyboard, parse_mode='HTML' if inline_buttons else None)
                    else:
                        self.ctx.bot.send_document(uid, reply.document.file_id, reply_markup=keyboard)
                else:
                    if clean_text:
                        self.ctx.bot.send_message(uid, clean_text, entities=entities if not inline_buttons else None, reply_markup=keyboard, parse_mode='HTML' if inline_buttons else None)
                success += 1
            except:
                failed += 1

        with ThreadPoolExecutor(max_workers=10) as ex:
            list(ex.map(send_to, users))
        Database.log_action(message.from_user.id, 'spam', details=f'success={success} failed={failed}')
        self.ctx.bot.edit_message_text(f"✅ <b>Рассылка завершена!</b>\n\n📤 Отправлено: <b>{success}</b>\n❌ Ошибок: <b>{failed}</b>", message.chat.id, status_msg.message_id, parse_mode='HTML')

    def handle_debug(self, message):
        cid = message.chat.id
        Database.add_user(cid, message.from_user.username, message.from_user.first_name)
        di = [f"👤 User ID: {cid}", f"📊 States: {len(StateManager.user_states.get(cid, []))}", f"🎵 Track data: {'Yes' if cid in StateManager.user_track_data else 'No'}", f"⚙️ has_edit: {Database.get_has_edit(cid)}", f"💾 DB users: {Database.get_user_count()}", f"🕐 Boot time: {datetime.fromtimestamp(self.ctx.boot_time).strftime('%H:%M:%S')}", f"📢 Ad counter: {Database.get_ad_counter(cid)}"]
        if cid in StateManager.user_track_data:
            td = StateManager.user_track_data[cid]
            di.extend([f"📁 File: {td.get('file_path', 'None')}", f"⏳ Waiting: {td.get('waiting_for', 'None')}"])
        self.ctx.bot.send_message(cid, "<b>Debug:</b>\n" + "\n".join(di), parse_mode='HTML')

    def handle_clear(self, message):
        cid = message.chat.id
        Database.add_user(cid, message.from_user.username, message.from_user.first_name)
        StateManager.clear_user(cid)
        self.ctx.bot.send_message(cid, f'{Emoji.SUCCESS} <b>Очищено</b>', parse_mode='HTML')

    def handle_photo(self, message):
        cid = message.chat.id
        Database.add_user(cid, message.from_user.username, message.from_user.first_name)
        if cid in StateManager.user_track_data and StateManager.user_track_data[cid].get('waiting_for') == 'cover':
            try:
                fi = self.ctx.bot.get_file(message.photo[-1].file_id)
                df = self.ctx.bot.download_file(fi.file_path)
                fp = StateManager.user_track_data[cid]['file_path']
                if TagManager.set_cover(fp, df):
                    StateManager.user_track_data[cid]['waiting_for'] = None
                    td = StateManager.user_track_data[cid]
                    Database.log_action(cid, 'edit_tag', details='cover_changed', track_title=td.get('title'), artist_name=td.get('artist'))
                    self.ctx.bot.send_message(cid, f'{Emoji.MUSIC} <b>Редактирование</b>\n\n{Emoji.NOTE} Название: <b>{td["title"]}</b>\n{Emoji.USER} Автор: <b>{td["artist"]}</b>\n\n{Emoji.SUCCESS} Обложка обновлена!', reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
                else:
                    self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Ошибка</b>', parse_mode='HTML')
                try:
                    self.ctx.bot.delete_message(cid, message.message_id)
                except:
                    pass
            except Exception as e:
                logger.error(f"Photo error for {cid}: {e}")
                self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Ошибка:</b> {e}', parse_mode='HTML')

    def handle_d_command(self, message):
        cid = message.chat.id
        if message.from_user.id not in Config.ADMIN_IDS:
            self.ctx.bot.send_message(cid, "❌ <b>Нет доступа</b>", parse_mode='HTML')
            return
        parts = message.text.split()
        if len(parts) != 2:
            self.ctx.bot.send_message(cid, "❌ <b>Использование:</b> /d <user_id>", parse_mode='HTML')
            return
        try:
            tid = int(parts[1])
            with sqlite3.connect(Config.DB_NAME) as conn:
                r = conn.execute('SELECT added_date FROM users WHERE user_id = ?', (tid,)).fetchone()
                if r:
                    ts = int(datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S').timestamp())
                    bi = self.ctx.bot.get_me()
                    self.ctx.bot.send_message(cid, f'{Emoji.SUCCESS} <b>Ссылка для {tid}</b>\n\n📅 <code>{r[0]}</code>\n⏱ <code>{ts}</code>\n\n🔗 https://t.me/{bi.username}?start=user_{ts}', parse_mode='HTML')
                else:
                    self.ctx.bot.send_message(cid, f"❌ <b>Пользователь {tid} не найден</b>", parse_mode='HTML')
        except Exception as e:
            self.ctx.bot.send_message(cid, f"❌ <b>Ошибка:</b> {e}", parse_mode='HTML')
