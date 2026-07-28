import json
import os
import re
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

from ym_bot.logger import logger

ROOT_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT_DIR / 'settings.json'
ENV_PATH = ROOT_DIR / '.env'
ENV_EXAMPLE_PATH = ROOT_DIR / '.env.example'

YM_CLIENT_ID = '23cabbbdc6cd418e8cc3b623496c229'
YM_CLIENT_SECRET = '53bc75205ef39cdd4189d753763b047e'

ENV_MAP = {
    'ym_token': 'YM_TOKEN',
    'ym_session_id': 'YM_SESSION_ID',
    'bot_token': 'BOT_TOKEN',
    'vk_token': 'VK_TOKEN',
    'admin_ids': 'ADMIN_IDS',
    'channel_id': 'CHANNEL_ID',
    'channel_username': 'CHANNEL_USERNAME',
    'channel_link': 'CHANNEL_LINK',
    'output_dir': 'OUTPUT_DIR',
    'media_dir': 'MEDIA_DIR',
    'db_name': 'DB_NAME',
    'audio_bitrate': 'AUDIO_BITRATE',
}


class EnvFile:
    @staticmethod
    def ensure():
        if ENV_PATH.exists():
            return
        if ENV_EXAMPLE_PATH.exists():
            ENV_PATH.write_text(ENV_EXAMPLE_PATH.read_text(encoding='utf-8'), encoding='utf-8')
            return
        ENV_PATH.write_text('\n'.join(f'{env_key}=\n' for env_key in ENV_MAP.values()) + '\n', encoding='utf-8')

    @staticmethod
    def upsert(key: str, value: str):
        EnvFile.ensure()
        lines = ENV_PATH.read_text(encoding='utf-8').splitlines()
        updated = []
        found = False
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or '=' not in line:
                updated.append(line)
                continue
            current_key = line.split('=', 1)[0].strip()
            if current_key == key:
                updated.append(f'{key}={value}')
                found = True
            else:
                updated.append(line)
        if not found:
            updated.append(f'{key}={value}')
        ENV_PATH.write_text('\n'.join(updated).rstrip() + '\n', encoding='utf-8')

    @staticmethod
    def parse_admin_ids(raw: str):
        if not raw:
            return []
        parts = []
        for chunk in raw.replace(';', ',').split(','):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                parts.append(int(chunk))
            except ValueError:
                continue
        return parts


class SettingsStore:
    DEFAULTS = {
        'ym_token': '',
        'ym_session_id': '',
        'bot_token': '',
        'vk_token': '',
        'admin_ids': [],
        'channel_id': -100,
        'channel_username': '',
        'channel_link': 'https://t.me/',
        'output_dir': 'downloads',
        'media_dir': 'media',
        'db_name': 'users.db',
        'audio_bitrate': 192,
    }

    def __init__(self, data=None):
        self.data = {**self.DEFAULTS, **(data or {})}

    @classmethod
    def _load_json(cls):
        if not SETTINGS_PATH.exists():
            return {}
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        except Exception as exc:
            logger.error(f'Failed to load settings.json: {exc}')
            return {}

    @classmethod
    def _overlay_env(cls, data: dict):
        EnvFile.ensure()
        load_dotenv(ENV_PATH, override=True)
        for data_key, env_key in ENV_MAP.items():
            raw = os.getenv(env_key)
            if raw is None or raw == '':
                continue
            if data_key == 'admin_ids':
                data[data_key] = EnvFile.parse_admin_ids(raw)
            elif data_key in {'channel_id', 'audio_bitrate'}:
                try:
                    data[data_key] = int(raw)
                except ValueError:
                    logger.error(f'Invalid integer in {env_key}')
            else:
                data[data_key] = raw
        return data

    @classmethod
    def load(cls):
        merged = cls._overlay_env({**cls.DEFAULTS, **cls._load_json()})
        return cls(merged)

    def save(self):
        SETTINGS_PATH.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, persist_env=True):
        self.data[key] = value
        self.save()
        if persist_env and key in ENV_MAP:
            if key == 'admin_ids':
                env_value = ','.join(str(item) for item in value)
            else:
                env_value = str(value)
            EnvFile.upsert(ENV_MAP[key], env_value)

    def apply_to_config(self):
        from ym_bot.config import Config

        Config.YM_TOKEN = self.data.get('ym_token') or ''
        Config.BOT_TOKEN = self.data.get('bot_token') or ''
        Config.ADMIN_IDS = list(self.data.get('admin_ids') or [])
        Config.CHANNEL_ID = int(self.data.get('channel_id', Config.CHANNEL_ID))
        Config.CHANNEL_USERNAME = self.data.get('channel_username') or ''
        Config.CHANNEL_LINK = self.data.get('channel_link') or Config.CHANNEL_LINK
        Config.VK_TOKEN = self.data.get('vk_token') or ''
        Config.OUTPUT_DIR = self.data.get('output_dir') or 'downloads'
        Config.MEDIA_DIR = self.data.get('media_dir') or Config.MEDIA_DIR
        Config.DB_NAME = self.data.get('db_name') or Config.DB_NAME
        Config.AUDIO_BITRATE = int(self.data.get('audio_bitrate') or Config.AUDIO_BITRATE)

    @staticmethod
    def mask(value: str, visible=4):
        if not value:
            return '(empty)'
        if len(value) <= visible * 2:
            return '*' * len(value)
        return f'{value[:visible]}...{value[-visible:]}'

    @classmethod
    def parse_cookie_input(cls, raw: str) -> dict:
        cookies = {}
        text = raw.strip()
        if not text:
            return cookies
        if '\t' in text and text.count('\t') >= 6:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
            return cookies
        for chunk in re.split(r'[;\n]', text):
            chunk = chunk.strip()
            if not chunk or '=' not in chunk:
                continue
            name, value = chunk.split('=', 1)
            cookies[name.strip()] = value.strip()
        if '=' not in text and '\n' not in text and ';' not in text:
            cookies['Session_id'] = text
        return cookies

    @classmethod
    def token_from_session_id(cls, session_id: str) -> Optional[str]:
        try:
            resp = requests.post(
                'https://mobileproxy.passport.yandex.net/1/bundle/oauth/token_by_sessionid',
                data={
                    'client_id': YM_CLIENT_ID,
                    'client_secret': YM_CLIENT_SECRET,
                    'sessionid': session_id,
                },
                headers={'User-Agent': 'com.yandex.mobile.auth.sdk/7.27.0.933787'},
                timeout=20,
            )
            if resp.status_code != 200:
                logger.error(f'Session exchange failed: {resp.status_code} {resp.text[:200]}')
                return None
            payload = resp.json()
            return payload.get('access_token') or payload.get('token')
        except Exception as exc:
            logger.error(f'Session exchange error: {exc}')
            return None

    def import_cookies(self, raw: str) -> tuple:
        cookies = self.parse_cookie_input(raw)
        session_id = cookies.get('Session_id') or cookies.get('sessionid')
        if not session_id:
            return False, 'Session_id не найден. Вставьте cookie целиком или только значение Session_id.'
        token = self.token_from_session_id(session_id)
        if not token:
            return False, 'Не удалось получить OAuth-токен из Session_id. Проверьте cookie или используйте auth ym-token.'
        self.set('ym_session_id', session_id)
        self.set('ym_token', token)
        return True, f'Токен сохранён: {self.mask(token)}'

    def status_lines(self):
        return [
            f'env: {ENV_PATH}',
            f'settings: {SETTINGS_PATH}',
            f'YM_TOKEN: {self.mask(self.data.get("ym_token", ""))}',
            f'YM_SESSION_ID: {self.mask(self.data.get("ym_session_id", ""))}',
            f'BOT_TOKEN: {self.mask(self.data.get("bot_token", ""))}',
            f'VK_TOKEN: {self.mask(self.data.get("vk_token", ""))}',
            f'ADMIN_IDS: {self.data.get("admin_ids") or []}',
            f'CHANNEL_USERNAME: {self.data.get("channel_username") or "(empty)"}',
            f'CHANNEL_LINK: {self.data.get("channel_link") or "(empty)"}',
            f'OUTPUT_DIR: {self.data.get("output_dir") or "downloads"}',
            f'MEDIA_DIR: {self.data.get("media_dir") or "media"}',
            f'DB_NAME: {self.data.get("db_name") or "users.db"}',
            f'AUDIO_BITRATE: {self.data.get("audio_bitrate") or 192}',
        ]
