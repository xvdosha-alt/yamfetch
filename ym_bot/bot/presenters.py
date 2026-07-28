from ym_bot.persistence.database import Database


class AdminPresenter:
    @staticmethod
    def _user_display(ud):
        uid = ud.get('user_id', '?')
        if ud.get('username'):
            return f"@{ud['username']} ({uid})"
        if ud.get('first_name'):
            return f"{ud['first_name']} ({uid})"
        return str(uid)

    def _format_admin_global_stats(self):
        s = Database.get_global_stats()
        return f'📊 <b>Общая статистика</b>\n\n👥 Пользователей: <b>{s.get("total_users",0)}</b>\n⬇️ Скачиваний: <b>{s.get("total_downloads",0)}</b>\n🎵 VK: <b>{s.get("vk_downloads",0)}</b>\n🔍 Поисков: <b>{s.get("total_searches",0)}</b>\n🎛 Эффектов: <b>{s.get("total_effects",0)}</b>\n✏️ Редактирований: <b>{s.get("total_edits",0)}</b>\n📀 Альбомов: <b>{s.get("total_album_downloads",0)}</b>\n▶️ Плейлистов: <b>{s.get("total_playlist_downloads",0)}</b>\n👤 Скачивали: <b>{s.get("users_who_downloaded",0)}</b>\n❌ Ошибок: <b>{s.get("total_errors",0)}</b>\n\n📅 <b>Сегодня:</b>\n📊 {s.get("today_actions",0)} | ⬇️ {s.get("today_downloads",0)} | 👥 {s.get("today_active_users",0)} | 🆕 {s.get("today_new_users",0)}'

    def _format_top_list(self, title, items, vk, label, se=None):
        if not items:
            return f"{title}\n\nПусто"
        lines = [title, ""]
        for i, item in enumerate(items, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            extra = f" ({item[se]})" if se and item.get(se) else ""
            lines.append(f"{medal} {self._user_display(item)} — <b>{item.get(vk,0)}</b> {label}{extra}")
        return "\n".join(lines)
