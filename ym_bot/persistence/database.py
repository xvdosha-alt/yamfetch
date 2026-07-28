import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ym_bot.config import Config
from ym_bot.logger import logger


class Database:
    _lock = threading.Lock()

    @classmethod
    def init(cls):
        try:
            with sqlite3.connect(Config.DB_NAME) as conn:
                conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, added_date TEXT NOT NULL, has_edit INTEGER DEFAULT 1, username TEXT DEFAULT NULL, first_name TEXT DEFAULT NULL, ad_counter INTEGER DEFAULT 0)')
                conn.execute('CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, action_type TEXT NOT NULL, details TEXT DEFAULT NULL, track_title TEXT DEFAULT NULL, artist_name TEXT DEFAULT NULL, source TEXT DEFAULT \'yandex\', tracks_count INTEGER DEFAULT 0, album_title TEXT DEFAULT NULL, playlist_title TEXT DEFAULT NULL, effect_name TEXT DEFAULT NULL, success INTEGER DEFAULT 1, error_text TEXT DEFAULT NULL, created_at TEXT NOT NULL)')
                conn.execute('CREATE TABLE IF NOT EXISTS daily_stats (date TEXT PRIMARY KEY, total_downloads INTEGER DEFAULT 0, total_searches INTEGER DEFAULT 0, total_effects INTEGER DEFAULT 0, total_edits INTEGER DEFAULT 0, unique_users INTEGER DEFAULT 0, new_users INTEGER DEFAULT 0, vk_downloads INTEGER DEFAULT 0, album_downloads INTEGER DEFAULT 0, playlist_downloads INTEGER DEFAULT 0)')
                conn.commit()
                columns = [col[1] for col in conn.execute("PRAGMA table_info(users)").fetchall()]
                for col, default in [('has_edit', '1'), ('username', 'NULL'), ('first_name', 'NULL'), ('ad_counter', '0')]:
                    if col not in columns:
                        conn.execute(f'ALTER TABLE users ADD COLUMN {col} {"INTEGER" if col in ("has_edit","ad_counter") else "TEXT"} DEFAULT {default}')
                conn.commit()
                logger.info("Database initialized")
        except Exception as e:
            logger.error(f"DB init error: {e}")

    @classmethod
    def add_user(cls, user_id: int, username: str = None, first_name: str = None):
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    conn.execute('INSERT OR IGNORE INTO users (user_id, added_date, has_edit, username, first_name, ad_counter) VALUES (?, ?, 1, ?, ?, 0)', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username, first_name))
                    if username or first_name:
                        conn.execute('UPDATE users SET username = COALESCE(?, username), first_name = COALESCE(?, first_name) WHERE user_id = ?', (username, first_name, user_id))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    @classmethod
    def get_ad_counter(cls, user_id: int) -> int:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    r = conn.execute('SELECT ad_counter FROM users WHERE user_id = ?', (user_id,)).fetchone()
                    return r[0] if r else 0
        except:
            return 0

    @classmethod
    def increment_ad_counter(cls, user_id: int) -> int:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    r = conn.execute('SELECT ad_counter FROM users WHERE user_id = ?', (user_id,)).fetchone()
                    current = (r[0] if r else 0) + 1
                    if current >= Config.AD_CYCLE:
                        conn.execute('UPDATE users SET ad_counter = 0 WHERE user_id = ?', (user_id,))
                        conn.commit()
                        return Config.AD_CYCLE
                    conn.execute('UPDATE users SET ad_counter = ? WHERE user_id = ?', (current, user_id))
                    conn.commit()
                    return current
        except:
            return 0

    @classmethod
    def reset_ad_counter(cls, user_id: int):
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    conn.execute('UPDATE users SET ad_counter = 0 WHERE user_id = ?', (user_id,))
                    conn.commit()
        except:
            pass

    @classmethod
    def log_action(cls, user_id: int, action_type: str, details: str = None, track_title: str = None, artist_name: str = None, source: str = 'yandex', tracks_count: int = 0, album_title: str = None, playlist_title: str = None, effect_name: str = None, success: int = 1, error_text: str = None):
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute('INSERT INTO actions (user_id, action_type, details, track_title, artist_name, source, tracks_count, album_title, playlist_title, effect_name, success, error_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (user_id, action_type, details, track_title, artist_name, source, tracks_count, album_title, playlist_title, effect_name, success, error_text, now))
                    today = datetime.now().strftime('%Y-%m-%d')
                    conn.execute('INSERT OR IGNORE INTO daily_stats (date) VALUES (?)', (today,))
                    col_map = {'download_track': 'total_downloads', 'search': 'total_searches', 'apply_effect': 'total_effects', 'edit_tag': 'total_edits', 'download_album': 'album_downloads', 'download_playlist': 'playlist_downloads'}
                    if action_type in col_map:
                        conn.execute(f'UPDATE daily_stats SET {col_map[action_type]} = {col_map[action_type]} + 1 WHERE date = ?', (today,))
                    if action_type == 'download_track' and source == 'vk':
                        conn.execute('UPDATE daily_stats SET vk_downloads = vk_downloads + 1 WHERE date = ?', (today,))
                    conn.commit()
            logger.info(f"ACTION: user={user_id} type={action_type} track={track_title} artist={artist_name} source={source} success={success}")
        except Exception as e:
            logger.error(f"Error logging action: {e}")

    @classmethod
    def update_daily_unique_users(cls):
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    today = datetime.now().strftime('%Y-%m-%d')
                    unique = conn.execute("SELECT COUNT(DISTINCT user_id) FROM actions WHERE created_at LIKE ?", (f"{today}%",)).fetchone()[0]
                    new = conn.execute("SELECT COUNT(*) FROM users WHERE added_date LIKE ?", (f"{today}%",)).fetchone()[0]
                    conn.execute('INSERT OR IGNORE INTO daily_stats (date) VALUES (?)', (today,))
                    conn.execute('UPDATE daily_stats SET unique_users = ?, new_users = ? WHERE date = ?', (unique, new, today))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error updating daily unique users: {e}")

    @classmethod
    def get_has_edit(cls, user_id: int) -> int:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    r = conn.execute('SELECT has_edit FROM users WHERE user_id = ?', (user_id,)).fetchone()
                    return r[0] if r else 1
        except:
            return 1

    @classmethod
    def toggle_has_edit(cls, user_id: int) -> int:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    r = conn.execute('SELECT has_edit FROM users WHERE user_id = ?', (user_id,)).fetchone()
                    new_val = 0 if (r[0] if r else 1) == 1 else 1
                    conn.execute('UPDATE users SET has_edit = ? WHERE user_id = ?', (new_val, user_id))
                    conn.commit()
                    return new_val
        except:
            return 1

    @classmethod
    def get_user_count(cls) -> int:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        except:
            return 0

    @classmethod
    def get_all_users(cls) -> List[int]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [r[0] for r in conn.execute('SELECT user_id FROM users').fetchall()]
        except:
            return []

    @classmethod
    def get_user_by_timestamp(cls, timestamp: int) -> Optional[Dict]:
        try:
            target = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    r = conn.execute('SELECT user_id, added_date, has_edit FROM users WHERE added_date = ?', (target,)).fetchone()
                    return {'user_id': r[0], 'added_date': r[1], 'has_edit': r[2]} if r else None
        except:
            return None

    @classmethod
    def get_global_stats(cls) -> Dict:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    s = {}
                    s['total_users'] = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                    for k, q in [('total_downloads', "action_type='download_track'"), ('vk_downloads', "action_type='download_track' AND source='vk'"), ('total_searches', "action_type='search'"), ('total_effects', "action_type='apply_effect'"), ('total_edits', "action_type='edit_tag'"), ('total_album_downloads', "action_type='download_album'"), ('total_playlist_downloads', "action_type='download_playlist'"), ('users_who_downloaded', None), ('total_errors', "success=0")]:
                        if k == 'users_who_downloaded':
                            s[k] = conn.execute("SELECT COUNT(DISTINCT user_id) FROM actions WHERE action_type='download_track'").fetchone()[0]
                        else:
                            s[k] = conn.execute(f'SELECT COUNT(*) FROM actions WHERE {q}').fetchone()[0]
                    today = datetime.now().strftime('%Y-%m-%d')
                    s['today_actions'] = conn.execute('SELECT COUNT(*) FROM actions WHERE created_at LIKE ?', (f"{today}%",)).fetchone()[0]
                    s['today_downloads'] = conn.execute("SELECT COUNT(*) FROM actions WHERE action_type='download_track' AND created_at LIKE ?", (f"{today}%",)).fetchone()[0]
                    s['today_active_users'] = conn.execute('SELECT COUNT(DISTINCT user_id) FROM actions WHERE created_at LIKE ?', (f"{today}%",)).fetchone()[0]
                    s['today_new_users'] = conn.execute('SELECT COUNT(*) FROM users WHERE added_date LIKE ?', (f"{today}%",)).fetchone()[0]
                    return s
        except:
            return {}

    @classmethod
    def get_top_users_by_downloads(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'count': r[3]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, COUNT(*) as cnt FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.action_type='download_track' AND a.success=1 GROUP BY a.user_id ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_top_users_by_searches(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'count': r[3]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, COUNT(*) as cnt FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.action_type='search' GROUP BY a.user_id ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_top_users_by_effects(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'count': r[3]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, COUNT(*) as cnt FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.action_type='apply_effect' GROUP BY a.user_id ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_top_album_downloads(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'album_title': r[3], 'tracks_count': r[4], 'created_at': r[5]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, a.album_title, a.tracks_count, a.created_at FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.action_type='download_album' AND a.success=1 ORDER BY a.tracks_count DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_top_playlist_downloads(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'playlist_title': r[3], 'tracks_count': r[4], 'created_at': r[5]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, a.playlist_title, a.tracks_count, a.created_at FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.action_type='download_playlist' AND a.success=1 ORDER BY a.tracks_count DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_most_downloaded_tracks(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'track_title': r[0], 'artist_name': r[1], 'count': r[2]} for r in conn.execute("SELECT track_title, artist_name, COUNT(*) as cnt FROM actions WHERE action_type='download_track' AND success=1 AND track_title IS NOT NULL GROUP BY track_title, artist_name ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_most_used_effects(cls) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'effect_name': r[0], 'count': r[1]} for r in conn.execute("SELECT effect_name, COUNT(*) as cnt FROM actions WHERE action_type='apply_effect' AND effect_name IS NOT NULL GROUP BY effect_name ORDER BY cnt DESC").fetchall()]
        except:
            return []

    @classmethod
    def get_recent_actions(cls, limit=20) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'first_name': r[2], 'action_type': r[3], 'track_title': r[4], 'artist_name': r[5], 'source': r[6], 'success': r[7], 'created_at': r[8], 'details': r[9], 'album_title': r[10], 'playlist_title': r[11], 'effect_name': r[12], 'tracks_count': r[13]} for r in conn.execute("SELECT a.user_id, u.username, u.first_name, a.action_type, a.track_title, a.artist_name, a.source, a.success, a.created_at, a.details, a.album_title, a.playlist_title, a.effect_name, a.tracks_count FROM actions a LEFT JOIN users u ON a.user_id=u.user_id ORDER BY a.id DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_recent_errors(cls, limit=10) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    return [{'user_id': r[0], 'username': r[1], 'action_type': r[2], 'error_text': r[3], 'created_at': r[4]} for r in conn.execute("SELECT a.user_id, u.username, a.action_type, a.error_text, a.created_at FROM actions a LEFT JOIN users u ON a.user_id=u.user_id WHERE a.success=0 ORDER BY a.id DESC LIMIT ?", (limit,)).fetchall()]
        except:
            return []

    @classmethod
    def get_daily_stats_range(cls, days=7) -> List[Dict]:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    cursor = conn.execute('SELECT * FROM daily_stats WHERE date >= ? ORDER BY date DESC', (start,))
                    cols = [d[0] for d in cursor.description]
                    return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except:
            return []

    @classmethod
    def get_user_stats(cls, user_id: int) -> Dict:
        try:
            with cls._lock:
                with sqlite3.connect(Config.DB_NAME) as conn:
                    s = {}
                    r = conn.execute('SELECT username, first_name, added_date, has_edit FROM users WHERE user_id = ?', (user_id,)).fetchone()
                    if r:
                        s['username'], s['first_name'], s['added_date'], s['has_edit'] = r
                    for k, at in [('downloads', 'download_track'), ('searches', 'search'), ('effects', 'apply_effect'), ('edits', 'edit_tag'), ('album_downloads', 'download_album'), ('playlist_downloads', 'download_playlist')]:
                        s[k] = conn.execute(f"SELECT COUNT(*) FROM actions WHERE user_id=? AND action_type=?", (user_id, at)).fetchone()[0]
                    r2 = conn.execute("SELECT MAX(tracks_count) FROM actions WHERE user_id=? AND action_type IN ('download_album','download_playlist')", (user_id,)).fetchone()
                    s['max_batch_size'] = r2[0] if r2 and r2[0] else 0
                    return s
        except:
            return {}
