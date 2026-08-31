[EN](../README.md) | RU

## yamfetch 🎵

Telegram-бот и CLI для скачивания музыки из Яндекс.Музыки (MP3 192 kbps).
Опционально - VK Music для поиска версий без цензуры в боте.

**yamfetch** = **Ya**ndex **M**usic **fetch**

## 🚀 Быстрый старт

### Установка

```bash
git clone https://github.com/xvDoshik/yamfetch.git
cd yamfetch
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

На macOS для `pydub` может понадобиться ffmpeg:

```bash
brew install ffmpeg
```

### 1. Настройка `.env`

```bash
cp .env.example .env
```

| Переменная | Описание |
|---|---|
| `YM_TOKEN` | OAuth-токен Яндекс.Музыки |
| `YM_SESSION_ID` | Session_id (опционально) |
| `BOT_TOKEN` | Telegram bot token |
| `VK_TOKEN` | VK token (опционально) |
| `ADMIN_IDS` | ID админов через запятую: `123,456` |
| `CHANNEL_USERNAME` | Username канала для подписки |
| `CHANNEL_LINK` | Ссылка на канал |
| `OUTPUT_DIR` | Папка для CLI-скачиваний |
| `MEDIA_DIR` | Временная папка бота |
| `DB_NAME` | Файл SQLite |
| `AUDIO_BITRATE` | Битрейт MP3 (по умолчанию 192) |

Приоритет: **`.env` → `settings.json` → defaults**

```bash
python downld.py auth
```

### 2. Доступ к Яндекс.Музыке

```bash
python downld.py auth
python downld.py auth ym-token
python downld.py auth ym-cookie
python downld.py auth test
```

#### OAuth token

1. [music.yandex.ru](https://music.yandex.ru) → войти
2. DevTools → Application → Local Storage / Cookies
3. `python downld.py auth ym-token`

#### Cookie / Session_id

1. Скопируй `Session_id` из cookies
2. `python downld.py auth ym-cookie`
3. Вставь значение, строку `Session_id=...` или Netscape `cookies.txt`

### 3. CLI

```bash
python downld.py cli search -q "molchat doma sudno"
python downld.py cli download -q "molchat doma sudno"
python downld.py cli download -q "molchat doma sudno" --index 2
python downld.py cli download -u "https://music.yandex.ru/album/123/track/456"
python downld.py cli download -q "artist track" -o ./my_music
```

### 4. Telegram-бот

```bash
python downld.py auth bot-token
python downld.py bot
```

```env
ADMIN_IDS=123456789
CHANNEL_USERNAME=your_channel
CHANNEL_LINK=https://t.me/your_channel
```

Команды: `/start`, `/help`, `/has_edit`, `/admin`, `/stats`, `/clear`

## 📋 Команды

| Команда | Описание |
|---|---|
| `python downld.py bot` | Telegram-бот |
| `python downld.py auth` | Настройка |
| `python downld.py auth show` | Текущие настройки |
| `python downld.py auth ym-token` | Yandex OAuth |
| `python downld.py auth ym-cookie` | Cookie / Session_id |
| `python downld.py auth bot-token` | Telegram token |
| `python downld.py auth test` | Проверка API |
| `python downld.py cli search -q "..."` | Поиск |
| `python downld.py cli download -q "..."` | Скачать |
| `python downld.py cli download -u URL` | Скачать по ссылке |

После `pip install -e .` доступна команда `yamfetch` с теми же subcommands.

## Структура

```
yamfetch/
├── downld.py
├── pyproject.toml
├── .env.example
├── ym_bot/
│   ├── application.py
│   ├── settings.py
│   ├── cli/
│   ├── api/
│   ├── bot/
│   └── services/
└── downloads/
```

## Безопасность

- Не коммить `.env` и `settings.json`
- Используй только свой аккаунт Яндекс.Музыки
