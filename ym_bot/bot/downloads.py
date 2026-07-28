import asyncio
import os

import requests

from ym_bot.api.vk import VKMusicAPI
from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.config import Config
from ym_bot.emoji import Emoji
from ym_bot.logger import logger
from ym_bot.persistence.database import Database
from ym_bot.services.ads import AdvertisementManager
from ym_bot.services.state import StateManager
from ym_bot.ui.keyboards import KeyboardBuilder


class DownloadService:
    def __init__(self, ctx):
        self.ctx = ctx

    def download_and_send_track(self, chat_id, track, show_status=True):
        filename = None
        try:
            performer = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
            title, duration = track.title, track.duration_ms // 1000 if hasattr(track, 'duration_ms') and track.duration_ms else 0
            filename = YandexMusicAPI.get_track_filename(track)
            track.download(filename, codec='mp3', bitrate_in_kbps=Config.AUDIO_BITRATE)
            abs_path = os.path.abspath(filename)
            self.ctx.bot.send_audio(chat_id, open(abs_path, 'rb'), title=title, performer=performer, duration=duration)
            Database.log_action(chat_id, 'download_track', track_title=title, artist_name=performer, source='yandex')
            self.ctx.bot.send_message(chat_id, f"<b>Есть цензура?</b> {Emoji.QUESTION}\n\n<i>Если в этом треке запиканы или вырезаны слова, попробуйте найти оригинальную версию в VK Music:</i>", reply_markup=KeyboardBuilder.create_vk_check_keyboard(f"{performer} {title}"), parse_mode='HTML')
            if show_status:
                self.ctx.bot.send_message(chat_id, f'{Emoji.SUCCESS} <b>Готово!</b>', parse_mode='HTML')
            AdvertisementManager.maybe_send_ad(self.ctx.bot, chat_id)
        except Exception as e:
            logger.error(f"Download error for {chat_id}: {e}")
            Database.log_action(chat_id, 'download_track', track_title=getattr(track, 'title', None), artist_name=', '.join(a.name for a in track.artists) if hasattr(track, 'artists') and track.artists else None, source='yandex', success=0, error_text=str(e))
            self.ctx.bot.send_message(chat_id, f'{Emoji.CANCEL} <b>Ошибка:</b> {str(e)}', parse_mode='HTML')
        finally:
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

    def download_vk_track(self, chat_id, owner_id, track_id):
        filename = None
        try:
            song = asyncio.run(VKMusicAPI.get_song_by_id(owner_id, track_id))
            if not song:
                Database.log_action(chat_id, 'download_track', source='vk', success=0, error_text='Not found')
                self.ctx.bot.send_message(chat_id, f"{Emoji.CANCEL} Трек в VK не найден.")
                return
            filename = f"{Config.MEDIA_DIR}/vk_{owner_id}_{track_id}.mp3"
            with open(filename, 'wb') as f:
                f.write(requests.get(song.url).content)
            with open(os.path.abspath(filename), 'rb') as af:
                self.ctx.bot.send_audio(chat_id, af, title=song.title, performer=song.artist)
            Database.log_action(chat_id, 'download_track', track_title=song.title, artist_name=song.artist, source='vk')
            AdvertisementManager.maybe_send_ad(self.ctx.bot, chat_id)
        except Exception as e:
            logger.error(f"VK download error for {chat_id}: {e}")
            Database.log_action(chat_id, 'download_track', source='vk', success=0, error_text=str(e))
            self.ctx.bot.send_message(chat_id, f"{Emoji.CANCEL} Ошибка VK: {e}")
        finally:
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

    def download_vk_for_edit(self, chat_id, owner_id, track_id):
        try:
            song = asyncio.run(VKMusicAPI.get_song_by_id(owner_id, track_id))
            if not song:
                return
            filename = f"{Config.MEDIA_DIR}/vk_edit_{chat_id}.mp3"
            with open(filename, 'wb') as f:
                f.write(requests.get(song.url).content)
            StateManager.user_track_data[chat_id] = {'file_path': filename, 'track_id': f"vk_{track_id}", 'title': song.title, 'artist': song.artist, 'waiting_for': None}
            self.ctx.bot.send_message(chat_id, f'{Emoji.MUSIC} <b>Редактирование (VK)</b>\n\n{song.artist} - {song.title}', reply_markup=KeyboardBuilder.create_track_edit_keyboard(), parse_mode='HTML')
        except Exception as e:
            logger.error(f"VK edit error for {chat_id}: {e}")
            self.ctx.bot.send_message(chat_id, f"❌ Ошибка VK: {e}")

    def download_track_for_edit(self, chat_id, track, message_id=None):
        filename = None
        try:
            filename = f"{Config.MEDIA_DIR}/{chat_id}_{track.id}.mp3"
            track.download(filename, codec='mp3', bitrate_in_kbps=Config.AUDIO_BITRATE)
            performer = ', '.join(a.name for a in track.artists) if track.artists else 'Unknown'
            StateManager.user_track_data[chat_id] = {'file_path': filename, 'track_id': track.id, 'title': track.title, 'artist': performer, 'waiting_for': None, 'original_track': track}
            text = f'{Emoji.MUSIC} <b>Редактирование трека</b>\n\n{Emoji.NOTE} Название: <b>{track.title}</b>\n{Emoji.USER} Автор: <b>{performer}</b>\n\nВыберите действие:'
            kb = KeyboardBuilder.create_track_edit_keyboard()
            if message_id:
                self.ctx.bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode='HTML')
            else:
                self.ctx.bot.send_message(chat_id, text, reply_markup=kb, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Edit download error for {chat_id}: {e}")
            self.ctx.bot.send_message(chat_id, f'{Emoji.CANCEL} <b>Ошибка:</b> {str(e)}', parse_mode='HTML')
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass
