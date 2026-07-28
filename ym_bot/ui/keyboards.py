from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ym_bot.api.yandex import YandexMusicAPI
from ym_bot.config import Config
from ym_bot.models import PlaylistInfo


class KeyboardBuilder:
    @staticmethod
    def create_track_edit_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("Название", callback_data="edit_title", icon_custom_emoji_id="5395444784611480792"), InlineKeyboardButton("Автор", callback_data="edit_artist", icon_custom_emoji_id="5879770735999717115"))
        kb.add(InlineKeyboardButton("Обложка", callback_data="edit_cover", icon_custom_emoji_id="5775949822993371030"))
        kb.add(InlineKeyboardButton("Эффекты", callback_data="show_effects", icon_custom_emoji_id="5875431869842985304"))
        kb.add(InlineKeyboardButton("Скачать", callback_data="download_edited", icon_custom_emoji_id="5899757765743615694"))
        kb.add(InlineKeyboardButton("Отмена", callback_data="cancel_edit", icon_custom_emoji_id="5210952531676504517"))
        return kb

    @staticmethod
    def create_effects_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("Slow", callback_data="effect_slow", icon_custom_emoji_id="5341715473882955310"), InlineKeyboardButton("Speed", callback_data="effect_speed", icon_custom_emoji_id="5235593631582858900"))
        kb.add(InlineKeyboardButton("Bass Boost", callback_data="effect_bass", icon_custom_emoji_id="5413879192523888818"), InlineKeyboardButton("Reverb", callback_data="effect_reverb", icon_custom_emoji_id="5407025283456835913"))
        kb.add(InlineKeyboardButton("Nightcore", callback_data="effect_nightcore", icon_custom_emoji_id="5409194415708749900"), InlineKeyboardButton("Vaporwave", callback_data="effect_vaporwave", icon_custom_emoji_id="5413361645498796498"))
        kb.add(InlineKeyboardButton("Назад", callback_data="back_to_edit", icon_custom_emoji_id="5420315771991497307"))
        return kb

    @staticmethod
    def create_single_track_keyboard(track_id, album_id=None):
        kb = InlineKeyboardMarkup(row_width=1)
        cb = f"quickdl_{track_id}_{album_id}" if album_id else f"quickdl_{track_id}"
        kb.add(InlineKeyboardButton("Быстрое скачивание", callback_data=cb, icon_custom_emoji_id="5899757765743615694"))
        ecb = f"edit_track_{track_id}_{album_id}" if album_id else f"edit_track_{track_id}"
        kb.add(InlineKeyboardButton("Редактировать и скачать", callback_data=ecb))
        return kb

    @staticmethod
    def create_search_type_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("Трек", callback_data="type_track", icon_custom_emoji_id="5292071317003069134"), InlineKeyboardButton("Альбом", callback_data="type_album", icon_custom_emoji_id="5258234027046883085"))
        kb.add(InlineKeyboardButton("Артист", callback_data="type_artist", icon_custom_emoji_id="5879770735999717115"), InlineKeyboardButton("Плейлист", callback_data="type_playlist", icon_custom_emoji_id="5348125953090403204"))
        return kb

    @staticmethod
    def create_ad_keyboard():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Подписаться", url=Config.CHANNEL_LINK, icon_custom_emoji_id="5458603043203327669"))
        return kb

    @staticmethod
    def create_admin_panel_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("📊 Общая статистика", callback_data="admin_global_stats"), InlineKeyboardButton("📅 За сегодня", callback_data="admin_today_stats"))
        kb.add(InlineKeyboardButton("🏆 Топ скачиваний", callback_data="admin_top_downloads"), InlineKeyboardButton("🔍 Топ поисков", callback_data="admin_top_searches"))
        kb.add(InlineKeyboardButton("🎛 Топ эффектов", callback_data="admin_top_effects"), InlineKeyboardButton("🎵 Популярные треки", callback_data="admin_popular_tracks"))
        kb.add(InlineKeyboardButton("📀 Топ альбомов", callback_data="admin_top_albums"), InlineKeyboardButton("▶️ Топ плейлистов", callback_data="admin_top_playlists"))
        kb.add(InlineKeyboardButton("📋 Последние действия", callback_data="admin_recent_actions"), InlineKeyboardButton("❌ Последние ошибки", callback_data="admin_recent_errors"))
        kb.add(InlineKeyboardButton("📈 Статистика за неделю", callback_data="admin_weekly_stats"), InlineKeyboardButton("🎛 Популярные эффекты", callback_data="admin_effect_stats"))
        kb.add(InlineKeyboardButton("👤 Инфо о пользователе", callback_data="admin_user_info"))
        return kb

    @staticmethod
    def create_paginated_keyboard(items, prefix, page=0, per_page=Config.PER_PAGE, get_text=None, has_back=False):
        if not items:
            return None
        if get_text is None:
            get_text = lambda item: (item.get('title') or item.get('name')) if isinstance(item, dict) else (getattr(item, 'title', None) or getattr(item, 'name', 'Unknown'))
        start, end = page * per_page, min((page + 1) * per_page, len(items))
        kb = InlineKeyboardMarkup(row_width=1)
        for item in items[start:end]:
            iid = item['id'] if isinstance(item, dict) else (getattr(item, 'kind', None) or getattr(item, 'id', None))
            if iid is not None:
                kb.add(InlineKeyboardButton(get_text(item), callback_data=f"{prefix}_{iid}", icon_custom_emoji_id="5292071317003069134"))
        tp = (len(items) + per_page - 1) // per_page
        if tp > 1:
            nav = []
            if page > 0:
                nav.append(InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
            nav.append(InlineKeyboardButton(f"{page+1}/{tp}", callback_data="ignore"))
            if page < tp - 1:
                nav.append(InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
            kb.row(*nav)
        if has_back:
            kb.add(InlineKeyboardButton("Назад", callback_data="back", icon_custom_emoji_id="5420315771991497307"))
        return kb

    @staticmethod
    def create_paginated_download_keyboard(tracks, page=0, album_id=None, playlist_info=None, per_page=Config.PER_PAGE, has_back=False):
        if not tracks:
            return None
        start, end = page * per_page, min((page + 1) * per_page, len(tracks))
        kb = InlineKeyboardMarkup(row_width=1)
        for track in tracks[start:end]:
            if album_id:
                tt = f"{track.title[:50]}"
            else:
                arts = ', '.join(a.name for a in track.artists)[:30] if track.artists else 'Unknown'
                tt = f"{track.title[:30]} - {arts}"
            aid = album_id or YandexMusicAPI.get_album_id(track)
            cb = f"select_{track.id}_{aid}" if aid else f"select_{track.id}"
            kb.add(InlineKeyboardButton(tt, callback_data=cb))
        if album_id:
            kb.add(InlineKeyboardButton("Скачать альбом", callback_data=f"download_album_{album_id}", icon_custom_emoji_id="5258234027046883085"))
        elif playlist_info:
            kb.add(InlineKeyboardButton("Скачать плейлист", callback_data=f"download_playlist_{playlist_info.owner}_{playlist_info.playlist_id}", icon_custom_emoji_id="5292071317003069134"))
        tp = (len(tracks) + per_page - 1) // per_page
        if tp > 1:
            nav = []
            if page > 0:
                nav.append(InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
            nav.append(InlineKeyboardButton(f"{page+1}/{tp}", callback_data="ignore"))
            if page < tp - 1:
                nav.append(InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
            kb.row(*nav)
        if has_back:
            kb.add(InlineKeyboardButton("Назад", callback_data="back", icon_custom_emoji_id="5420315771991497307"))
        return kb

    @staticmethod
    def create_vk_check_keyboard(query):
        kb = InlineKeyboardMarkup()
        truncated_query = query[:45]
        kb.add(InlineKeyboardButton("Найти в VK Music", callback_data=f"vk_srch_{truncated_query}", icon_custom_emoji_id="5429099542752561264"))
        return kb

    @staticmethod
    def create_vk_track_keyboard(owner_id, track_id):
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Быстрое скачивание", callback_data=f"vk_qdl_{owner_id}_{track_id}", icon_custom_emoji_id="5899757765743615694"), InlineKeyboardButton("✏️ Редактировать и скачать", callback_data=f"vk_edt_{owner_id}_{track_id}"), InlineKeyboardButton("🔙 Назад", callback_data="back_to_list"))
        return kb
