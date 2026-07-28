import asyncio
import os
import time

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ym_bot.api.vk import VKMusicAPI
from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.audio.effects import AudioEffects
from ym_bot.config import Config
from ym_bot.emoji import Emoji
from ym_bot.models import PlaylistInfo
from ym_bot.persistence.database import Database
from ym_bot.services.ads import AdvertisementManager
from ym_bot.services.state import StateManager
from ym_bot.ui.keyboards import KeyboardBuilder


class CallbackHandler:
    def __init__(self, ctx, downloads, presenter, navigation, commands):
        self.ctx = ctx
        self.downloads = downloads
        self.presenter = presenter
        self.navigation = navigation
        self.commands = commands

    def handle_callback(self, call):
        data, cid, mid = call.data, call.message.chat.id, call.message.message_id
        Database.add_user(cid, call.from_user.username, call.from_user.first_name)
        if data == 'ignore':
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_back':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            self.ctx.bot.edit_message_text(f"{Emoji.CROWN} <b>Админ-панель</b>\n\nВыберите раздел:", cid, mid, reply_markup=KeyboardBuilder.create_admin_panel_keyboard(), parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_global_stats':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            Database.update_daily_unique_users()
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text(self.presenter._format_admin_global_stats(), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_today_stats':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            Database.update_daily_unique_users()
            s = Database.get_global_stats()
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text(f'📅 <b>Сегодня</b>\n\n📊 {s.get("today_actions",0)} | ⬇️ {s.get("today_downloads",0)} | 👥 {s.get("today_active_users",0)} | 🆕 {s.get("today_new_users",0)}', cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_top_downloads':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text(self.presenter._format_top_list("🏆 <b>Топ скачиваний</b>", Database.get_top_users_by_downloads(10), 'count', 'скач.'), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_top_searches':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text(self.presenter._format_top_list("🔍 <b>Топ поисков</b>", Database.get_top_users_by_searches(10), 'count', 'поисков'), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_top_effects':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text(self.presenter._format_top_list("🎛 <b>Топ эффектов</b>", Database.get_top_users_by_effects(10), 'count', 'эфф.'), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_popular_tracks':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            tracks = Database.get_most_downloaded_tracks(10)
            lines = ["🎵 <b>Популярные треки</b>", ""]
            for i, t in enumerate(tracks, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(f"{medal} {t['artist_name'] or '?'} - {t['track_title'] or '?'} — <b>{t['count']}</b>")
            if not tracks:
                lines.append("Пусто")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_top_albums':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            top = Database.get_top_album_downloads(10)
            lines = ["📀 <b>Топ альбомов</b>", ""]
            for i, t in enumerate(top, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(f"{medal} {self.presenter._user_display(t)}\n   📀 {t.get('album_title','?')} — <b>{t.get('tracks_count',0)}</b> тр. | {t.get('created_at','?')}")
            if not top:
                lines.append("Пусто")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_top_playlists':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            top = Database.get_top_playlist_downloads(10)
            lines = ["▶️ <b>Топ плейлистов</b>", ""]
            for i, t in enumerate(top, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(f"{medal} {self.presenter._user_display(t)}\n   ▶️ {t.get('playlist_title','?')} — <b>{t.get('tracks_count',0)}</b> тр. | {t.get('created_at','?')}")
            if not top:
                lines.append("Пусто")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_recent_actions':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            actions = Database.get_recent_actions(15)
            lines = ["📋 <b>Последние действия</b>", ""]
            for a in actions:
                st = "✅" if a['success'] else "❌"
                un = f"@{a['username']}" if a.get('username') else str(a['user_id'])
                det = ""
                if a.get('track_title'):
                    det = f" | {a.get('artist_name','?')} - {a['track_title']}"
                elif a.get('album_title'):
                    det = f" | 📀 {a['album_title']} ({a.get('tracks_count',0)})"
                elif a.get('playlist_title'):
                    det = f" | ▶️ {a['playlist_title']} ({a.get('tracks_count',0)})"
                elif a.get('effect_name'):
                    det = f" | 🎛 {a['effect_name']}"
                elif a.get('details'):
                    det = f" | {a['details'][:40]}"
                src = f" [{a['source']}]" if a.get('source') and a['source'] != 'yandex' else ""
                ts = a['created_at'][11:16] if a.get('created_at') else '?'
                lines.append(f"{st} <code>{ts}</code> {un} → {a['action_type']}{src}{det}")
            if not actions:
                lines.append("Пусто")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_recent_errors':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            errors = Database.get_recent_errors(10)
            lines = ["❌ <b>Последние ошибки</b>", ""]
            for e in errors:
                un = f"@{e['username']}" if e.get('username') else str(e['user_id'])
                lines.append(f"❌ <code>{e['created_at'][11:16] if e.get('created_at') else '?'}</code> {un} → {e['action_type']}\n   <i>{(e.get('error_text') or 'Unknown')[:80]}</i>")
            if not errors:
                lines.append("Ошибок нет 🎉")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_weekly_stats':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            daily = Database.get_daily_stats_range(7)
            lines = ["📈 <b>За неделю</b>", ""]
            for d in daily:
                lines.append(f"📅 <b>{d['date']}</b>\n   ⬇️{d.get('total_downloads',0)} 🔍{d.get('total_searches',0)} 🎛{d.get('total_effects',0)} ✏️{d.get('total_edits',0)}\n   👥{d.get('unique_users',0)} 🆕{d.get('new_users',0)} VK:{d.get('vk_downloads',0)} 📀{d.get('album_downloads',0)} ▶️{d.get('playlist_downloads',0)}")
            if not daily:
                lines.append("Нет данных")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_effect_stats':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            effects = Database.get_most_used_effects()
            lines = ["🎛 <b>Популярные эффекты</b>", ""]
            for i, e in enumerate(effects, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(f"{medal} {e['effect_name']} — <b>{e['count']}</b>")
            if not effects:
                lines.append("Пусто")
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
            self.ctx.bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'admin_user_info':
            if call.from_user.id not in Config.ADMIN_IDS:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            StateManager.admin_waiting[cid] = 'user_info'
            self.ctx.bot.edit_message_text("👤 <b>Введите ID пользователя:</b>", cid, mid, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'main_menu':
            wt = f'{Emoji.HELLO}<b> Привет! </b>{Emoji.STAR}\n\n{Emoji.HEADPHONES} Я бот для скачивания музыки из <b>Яндекс.Музыки</b> {Emoji.NOTES}{Emoji.ROCKET}\n\n{Emoji.NOTE}<b> Отправь мне:</b>\n<blockquote>{Emoji.SEARCH} Название {Emoji.MIC}\n{Emoji.LINK} Ссылку {Emoji.DOWNLOAD}</blockquote>\n\n{Emoji.BULB} /help {Emoji.BOOK}{Emoji.QUESTION}'
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("Загрузить", url="https://t.me/YM_upload_bot", icon_custom_emoji_id="5899757765743615694"))
            kb.add(InlineKeyboardButton("Помощь", callback_data="show_help", icon_custom_emoji_id="5388953246486269495"))
            self.ctx.bot.edit_message_text(wt, cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'show_help':
            self.commands._send_help_message(cid, mid)
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'edit_title':
            if cid in StateManager.user_track_data:
                StateManager.user_track_data[cid]['waiting_for'] = 'title'
                self.ctx.bot.edit_message_text(f'{Emoji.EDIT} <b>Отправьте новое название:</b>', cid, mid, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'edit_artist':
            if cid in StateManager.user_track_data:
                StateManager.user_track_data[cid]['waiting_for'] = 'artist'
                self.ctx.bot.edit_message_text(f'{Emoji.USER} <b>Отправьте нового автора:</b>', cid, mid, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'edit_cover':
            if cid in StateManager.user_track_data:
                StateManager.user_track_data[cid]['waiting_for'] = 'cover'
                self.ctx.bot.edit_message_text(f'{Emoji.COVER} <b>Отправьте фото:</b>', cid, mid, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'show_effects':
            if cid in StateManager.user_track_data:
                td = StateManager.user_track_data[cid]
                self.ctx.bot.edit_message_text(f'{Emoji.EFFECTS} <b>Эффекты:</b>\n\n{Emoji.NOTE} <b>{td["title"]}</b>\n{Emoji.USER} <b>{td["artist"]}</b>', cid, mid, reply_markup=KeyboardBuilder.create_effects_keyboard(), parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'back_to_edit':
            if cid in StateManager.user_track_data:
                td = StateManager.user_track_data[cid]
                self.ctx.bot.edit_message_text(f'{Emoji.MUSIC} <b>Редактирование</b>\n\n{Emoji.NOTE} <b>{td["title"]}</b>\n{Emoji.USER} <b>{td["artist"]}</b>', cid, mid, reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data.startswith('effect_'):
            en = data.split('_')[1]
            if cid in StateManager.user_track_data:
                self.ctx.bot.answer_callback_query(call.id, f"⏳ {en}...")
                self.ctx.bot.edit_message_text(f'{Emoji.LOADING} <b>Применяю {en}...</b>', cid, mid, parse_mode='HTML')

                def ae():
                    try:
                        fp = StateManager.user_track_data[cid]['file_path']
                        np_ = AudioEffects.apply_effect(fp, en)
                        if np_ != fp:
                            StateManager.user_track_data[cid]['file_path'] = np_
                            if os.path.exists(fp):
                                os.remove(fp)
                        td = StateManager.user_track_data[cid]
                        Database.log_action(cid, 'apply_effect', effect_name=en, track_title=td.get('title'), artist_name=td.get('artist'))
                        self.ctx.bot.edit_message_text(f'{Emoji.MUSIC} <b>Редактирование</b>\n\n{Emoji.NOTE} <b>{td["title"]}</b>\n{Emoji.USER} <b>{td["artist"]}</b>\n\n{Emoji.SUCCESS} {en} применен!', cid, mid, reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
                    except Exception as e:
                        Database.log_action(cid, 'apply_effect', effect_name=en, success=0, error_text=str(e))
                        self.ctx.bot.edit_message_text(f'{Emoji.CANCEL} <b>Ошибка:</b> {e}', cid, mid, parse_mode='HTML')

                self.ctx.effect_executor.submit(ae)
            return
        if data == 'download_edited':
            if cid in StateManager.user_track_data:
                self.ctx.bot.answer_callback_query(call.id, "⏳...")

                def se():
                    try:
                        td = StateManager.user_track_data[cid]
                        with open(td['file_path'], 'rb') as af:
                            self.ctx.bot.send_audio(cid, af, title=td['title'], performer=td['artist'])
                        Database.log_action(cid, 'download_edited', track_title=td['title'], artist_name=td['artist'])
                        self.ctx.bot.edit_message_text(f'{Emoji.SUCCESS} <b>Готово!</b>', cid, mid, parse_mode='HTML')
                        if os.path.exists(td['file_path']):
                            os.remove(td['file_path'])
                        del StateManager.user_track_data[cid]
                        AdvertisementManager.maybe_send_ad(self.ctx.bot, cid)
                    except Exception as e:
                        self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Ошибка:</b> {e}', parse_mode='HTML')

                self.ctx.executor.submit(se)
            return
        if data == 'cancel_edit':
            if cid in StateManager.user_track_data:
                fp = StateManager.user_track_data[cid].get('file_path')
                if fp and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except:
                        pass
                del StateManager.user_track_data[cid]
            self.ctx.bot.edit_message_text(f'{Emoji.CANCEL} <b>Отменено</b>', cid, mid, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data.startswith('edit_track_'):
            parts = data.split('_')
            if len(parts) >= 3:
                tid, aid = parts[2], parts[3] if len(parts) > 3 and parts[3] != 'None' else None
                track = YandexMusicAPI.get_track(tid, aid)
                if track:
                    self.ctx.bot.answer_callback_query(call.id, "⏳...")
                    self.ctx.bot.edit_message_text(f'{Emoji.LOADING} <b>Загружаю...</b>', cid, mid, parse_mode='HTML')
                    self.ctx.executor.submit(self.downloads.download_track_for_edit, cid, track, mid)
                else:
                    self.ctx.bot.answer_callback_query(call.id, "❌")
            return
        if data.startswith('quickdl_'):
            parts = data.split('_')
            tid, aid = parts[1], parts[2] if len(parts) > 2 and parts[2] != 'None' else None
            track = YandexMusicAPI.get_track(tid, aid)
            if track:
                self.ctx.bot.answer_callback_query(call.id, "⏳...")
                self.ctx.executor.submit(self.downloads.download_and_send_track, cid, track)
            else:
                self.ctx.bot.answer_callback_query(call.id, "❌")
            return
        if data.startswith('select_'):
            parts = data.split('_')
            tid, aid = parts[1], parts[2] if len(parts) > 2 and parts[2] != 'None' else None
            track = YandexMusicAPI.get_track(tid, aid)
            if track:
                if Database.get_has_edit(cid) == 1:
                    perf = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
                    kb = KeyboardBuilder.create_single_track_keyboard(tid, aid)
                    kb.add(InlineKeyboardButton("Назад", callback_data="back_to_list", icon_custom_emoji_id="5420315771991497307"))
                    self.ctx.bot.send_message(cid, f'{Emoji.MUSIC} <b>{track.title}</b>\n{Emoji.USER} {perf}', reply_markup=kb, parse_mode='HTML')
                else:
                    self.ctx.bot.answer_callback_query(call.id, "⏳...")
                    self.ctx.executor.submit(self.downloads.download_and_send_track, cid, track)
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'back_to_list':
            self.navigation.restore_list_view(cid, mid)
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data == 'back':
            if cid in StateManager.user_states and len(StateManager.user_states[cid]) > 1:
                StateManager.user_states[cid].pop()
                self.navigation.restore_list_view(cid, mid)
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data.startswith('download_playlist_'):
            parts = data.split('_')[2:]
            if len(parts) >= 2:
                pi = PlaylistInfo(owner=parts[0], playlist_id=parts[1])
                self.ctx.bot.answer_callback_query(call.id, "⏳...")
                lm = self.ctx.bot.send_message(cid, f'{Emoji.LOADING} <b>Загрузка...</b>', parse_mode='HTML')

                def dpa():
                    pl = YandexMusicAPI.get_playlist(pi)
                    self.ctx.bot.delete_message(cid, lm.message_id)
                    if pl and pl.tracks:
                        tc = len(pl.tracks)
                        Database.log_action(cid, 'download_playlist', playlist_title=pl.title, tracks_count=tc)
                        self.ctx.bot.send_message(cid, f'{Emoji.LOADING} <b>Загрузка {tc} треков...</b>', parse_mode='HTML')
                        for i, t in enumerate(pl.tracks, 1):
                            if t:
                                if i > 1 and i % Config.BATCH_SIZE == 1:
                                    pm = self.ctx.bot.send_message(cid, f"⏸ <b>Пауза {Config.BATCH_WAIT}с...</b>", parse_mode='HTML')
                                    time.sleep(Config.BATCH_WAIT)
                                    try:
                                        self.ctx.bot.delete_message(cid, pm.message_id)
                                    except:
                                        pass
                                self.downloads.download_and_send_track(cid, t, show_status=False)
                        self.ctx.bot.send_message(cid, f'{Emoji.SUCCESS} <b>Плейлист загружен!</b>', parse_mode='HTML')
                    else:
                        Database.log_action(cid, 'download_playlist', success=0, error_text='Not found')
                        self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Не найден</b>', parse_mode='HTML')

                self.ctx.executor.submit(dpa)
            return
        if data.startswith('download_album_'):
            aid = data.split('_')[2]
            album = YandexMusicAPI.get_album(aid)
            if album:
                tracks = [t for vol in album.volumes for t in vol] if hasattr(album, 'volumes') and album.volumes else (album.tracks if hasattr(album, 'tracks') and album.tracks else [])
                arts = ', '.join(a.name for a in album.artists) if album.artists else 'Unknown'
                Database.log_action(cid, 'download_album', album_title=album.title, artist_name=arts, tracks_count=len(tracks))
                self.ctx.bot.answer_callback_query(call.id, "⏳...")
                self.ctx.bot.send_message(cid, f'{Emoji.LOADING} <b>Скачивание {len(tracks)} треков...</b>', parse_mode='HTML')

                def da():
                    for i, ts in enumerate(tracks, 1):
                        if i > 1 and i % Config.BATCH_SIZE == 1:
                            pm = self.ctx.bot.send_message(cid, f"⏸ <b>Пауза {Config.BATCH_WAIT}с...</b>", parse_mode='HTML')
                            time.sleep(Config.BATCH_WAIT)
                            try:
                                self.ctx.bot.delete_message(cid, pm.message_id)
                            except:
                                pass
                        track = YandexMusicAPI.get_track(ts.id, aid)
                        if track:
                            self.downloads.download_and_send_track(cid, track, show_status=False)
                    self.ctx.bot.send_message(cid, f'{Emoji.SUCCESS} <b>Альбом загружен!</b>', parse_mode='HTML')

                self.ctx.executor.submit(da)
            else:
                self.ctx.bot.answer_callback_query(call.id, '❌')
            return
        if data.startswith('page_'):
            try:
                page = int(data.split('_')[1])
            except:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            if cid not in StateManager.user_states or not StateManager.user_states[cid]:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            StateManager.user_states[cid][-1]['page'] = page
            self.navigation.restore_list_view(cid, mid)
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data.startswith('playlist_'):
            pk = data.split('_', 1)[1]
            if cid in StateManager.user_states and StateManager.user_states[cid]:
                state = StateManager.user_states[cid][-1]
                if state['type'] == 'playlists':
                    sp = next((p for p in state['items'] if str(p.kind) == pk), None)
                    if sp:
                        self.ctx.bot.answer_callback_query(call.id, "⏳...")
                        lm = self.ctx.bot.send_message(cid, f'{Emoji.LOADING} <b>Загрузка...</b>', parse_mode='HTML')

                        def ps():
                            try:
                                pi = PlaylistInfo(owner=sp.owner.uid if hasattr(sp.owner, 'uid') else sp.owner.login, playlist_id=str(sp.kind))
                                pl = YandexMusicAPI.get_playlist(pi)
                                self.ctx.bot.delete_message(cid, lm.message_id)
                                if pl and pl.tracks:
                                    lt = f" (первые {Config.MAX_PLAYLIST_TRACKS})" if len(pl.tracks) >= Config.MAX_PLAYLIST_TRACKS else ""
                                    txt = f'{Emoji.MUSIC} <b>{pl.title}</b>\n{Emoji.USER} {pl.owner.name}\n{Emoji.NOTES} {len(pl.tracks)} треков{lt}'
                                    hb = bool(StateManager.user_states.get(cid))
                                    kb = KeyboardBuilder.create_paginated_download_keyboard(pl.tracks, 0, playlist_info=pi, has_back=hb)
                                    if kb:
                                        if cid not in StateManager.user_states:
                                            StateManager.user_states[cid] = []
                                        StateManager.user_states[cid].append({'type': 'tracks', 'tracks': pl.tracks, 'album_id': None, 'playlist_info': pi, 'page': 0, 'label': txt})
                                        sm = self.ctx.bot.send_message(cid, txt, reply_markup=kb, parse_mode='HTML')
                                        StateManager.user_message_ids[cid] = sm.message_id
                                else:
                                    self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Не найден</b>', parse_mode='HTML')
                            except:
                                self.ctx.bot.delete_message(cid, lm.message_id)
                                self.ctx.bot.send_message(cid, f'{Emoji.CANCEL} <b>Ошибка</b>', parse_mode='HTML')

                        self.ctx.executor.submit(ps)
                    else:
                        self.ctx.bot.answer_callback_query(call.id, "❌")
            return
        if data.startswith('album_'):
            aid = data.split('_', 1)[1]
            album = YandexMusicAPI.get_album(aid)
            if album:
                tracks = [t for vol in album.volumes for t in vol] if hasattr(album, 'volumes') and album.volumes else (album.tracks if hasattr(album, 'tracks') and album.tracks else [])
                arts = ', '.join(a.name for a in album.artists) if album.artists else 'Unknown'
                txt = f'{Emoji.ALBUM} <b>{album.title}</b>\n{Emoji.USER} {arts}\n{Emoji.MUSIC} {len(tracks)} треков'
                hb = bool(StateManager.user_states.get(cid))
                kb = KeyboardBuilder.create_paginated_download_keyboard(tracks, 0, aid, has_back=hb)
                if kb:
                    if cid not in StateManager.user_states:
                        StateManager.user_states[cid] = []
                    StateManager.user_states[cid].append({'type': 'tracks', 'tracks': tracks, 'album_id': aid, 'playlist_info': None, 'page': 0, 'label': txt})
                    self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=kb, parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data.startswith('artist_'):
            arid = data.split('_', 1)[1]
            artist = YandexMusicAPI.get_artist(arid)
            if artist:
                albs = artist.get_albums()
                txt = f'{Emoji.USER} <b>{artist.name}</b>\n{Emoji.ALBUM} {len(albs)} альбомов'
                hb = bool(StateManager.user_states.get(cid))
                if albs:
                    if cid not in StateManager.user_states:
                        StateManager.user_states[cid] = []
                    StateManager.user_states[cid].append({'type': 'artist_albums', 'items': albs, 'page': 0, 'label': txt})
                    self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=KeyboardBuilder.create_paginated_keyboard(albs, 'album', 0, get_text=lambda i: f"{i.title} ({getattr(i, 'year', '?')})", has_back=hb), parse_mode='HTML')
            self.ctx.bot.answer_callback_query(call.id)
            return
        if data in ['type_track', 'type_album', 'type_artist', 'type_playlist']:
            query = StateManager.user_queries.get(cid)
            if not query:
                self.ctx.bot.answer_callback_query(call.id, "❌")
                return
            del StateManager.user_queries[cid]
            st = data.split('_')[1]
            try:
                if st == 'playlist':
                    pls = YandexMusicAPI.search_playlists(query)
                    txt = f'{Emoji.PLAYLIST} <b>Плейлисты</b>\n{Emoji.SEARCH} <i>{query}</i>\n\n{Emoji.STATS} Найдено: <b>{len(pls)}</b>'
                    if pls:
                        StateManager.user_states[cid] = [{'type': 'playlists', 'items': pls, 'page': 0, 'label': txt}]
                        self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=KeyboardBuilder.create_paginated_keyboard(pls, 'playlist', 0, get_text=lambda i: f"{i.title} - {i.owner.name if hasattr(i,'owner') else '?'} ({getattr(i,'track_count','?')})"), parse_mode='HTML')
                    else:
                        self.ctx.bot.edit_message_text(txt, cid, mid, parse_mode='HTML')
                else:
                    sr = YandexMusicAPI.search(query, st)
                    if st == 'track':
                        tracks = sr.tracks.results[:50] if sr and sr.tracks else []
                        txt = f'{Emoji.MUSIC} <b>Треки</b>\n{Emoji.SEARCH} <i>{query}</i>\n\n{Emoji.STATS} <b>{len(tracks)}</b>'
                        if tracks:
                            StateManager.user_states[cid] = [{'type': 'tracks', 'tracks': tracks, 'album_id': None, 'playlist_info': None, 'page': 0, 'label': txt}]
                            self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=KeyboardBuilder.create_paginated_download_keyboard(tracks, 0), parse_mode='HTML')
                        else:
                            self.ctx.bot.edit_message_text(txt, cid, mid, parse_mode='HTML')
                    elif st == 'album':
                        albums = sr.albums.results[:50] if sr and sr.albums else []
                        txt = f'{Emoji.ALBUM} <b>Альбомы</b>\n{Emoji.SEARCH} <i>{query}</i>\n\n{Emoji.STATS} <b>{len(albums)}</b>'
                        if albums:
                            StateManager.user_states[cid] = [{'type': 'albums', 'items': albums, 'page': 0, 'label': txt}]
                            self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=KeyboardBuilder.create_paginated_keyboard(albums, 'album', 0, get_text=lambda i: f"{i.title} ({getattr(i,'year','?')})"), parse_mode='HTML')
                        else:
                            self.ctx.bot.edit_message_text(txt, cid, mid, parse_mode='HTML')
                    elif st == 'artist':
                        artists = sr.artists.results[:50] if sr and sr.artists else []
                        txt = f'{Emoji.USER} <b>Артисты</b>\n{Emoji.SEARCH} <i>{query}</i>\n\n{Emoji.STATS} <b>{len(artists)}</b>'
                        if artists:
                            StateManager.user_states[cid] = [{'type': 'artists', 'items': artists, 'page': 0, 'label': txt}]
                            self.ctx.bot.edit_message_text(txt, cid, mid, reply_markup=KeyboardBuilder.create_paginated_keyboard(artists, 'artist', 0, get_text=lambda i: i.name), parse_mode='HTML')
                        else:
                            self.ctx.bot.edit_message_text(txt, cid, mid, parse_mode='HTML')
                AdvertisementManager.maybe_send_ad(self.ctx.bot, cid)
                self.ctx.bot.answer_callback_query(call.id)
            except:
                self.ctx.bot.answer_callback_query(call.id, "❌")
            return
        if data.startswith('vk_srch_'):
            query = data[8:]
            self.ctx.bot.answer_callback_query(call.id, "🔎...")
            Database.log_action(cid, 'search', details=f'vk: {query}', source='vk')
            songs = asyncio.run(VKMusicAPI.search_uncensored(query))
            if not songs:
                self.ctx.bot.send_message(cid, "😔 Не найдено в VK.")
                return
            kb = InlineKeyboardMarkup(row_width=1)
            for s in songs:
                kb.add(InlineKeyboardButton(f"{s.artist[:20]} - {s.title[:30]}", callback_data=f"vk_sel_{s.owner_id}_{s.track_id}"))
            self.ctx.bot.send_message(cid, f"{Emoji.SEARCH} <b>VK:</b>", reply_markup=kb, parse_mode='HTML')
            return
        if data.startswith('vk_sel_'):
            parts = data.split('_')
            oid, tid = parts[2], parts[3]
            if Database.get_has_edit(cid) == 1:
                self.ctx.bot.send_message(cid, f"{Emoji.MUSIC} <b>VK версия</b>", reply_markup=KeyboardBuilder.create_vk_track_keyboard(oid, tid), parse_mode='HTML')
            else:
                self.ctx.bot.answer_callback_query(call.id, "⏳...")
                self.ctx.executor.submit(self.downloads.download_vk_track, cid, oid, tid)
            return
        if data.startswith('vk_qdl_'):
            parts = data.split('_')
            self.ctx.bot.answer_callback_query(call.id, "⏳...")
            self.ctx.executor.submit(self.downloads.download_vk_track, cid, parts[2], parts[3])
            return
        if data.startswith('vk_edt_'):
            parts = data.split('_')
            self.ctx.bot.answer_callback_query(call.id, "⏳...")
            self.ctx.executor.submit(self.downloads.download_vk_for_edit, cid, parts[2], parts[3])
            return
        self.ctx.bot.answer_callback_query(call.id)
