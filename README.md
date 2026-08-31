EN | [RU](docs/README_RU.md)

## yamfetch 🎵

Telegram bot and CLI for downloading music from Yandex Music (MP3 192 kbps).
Optional VK Music integration for finding uncensored versions in the bot.

**yamfetch** = **Ya**ndex **M**usic **fetch**

## 🚀 Quick start

### Install

```bash
git clone https://github.com/xvDoshik/yamfetch.git
cd yamfetch
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On macOS, `pydub` may require ffmpeg:

```bash
brew install ffmpeg
```

### 1. Configure `.env`

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `YM_TOKEN` | Yandex Music OAuth token |
| `YM_SESSION_ID` | Session_id (optional) |
| `BOT_TOKEN` | Telegram bot token |
| `VK_TOKEN` | VK token (optional) |
| `ADMIN_IDS` | Admin IDs comma-separated: `123,456` |
| `CHANNEL_USERNAME` | Channel username for subscription check |
| `CHANNEL_LINK` | Channel link |
| `OUTPUT_DIR` | Folder for CLI downloads |
| `MEDIA_DIR` | Bot temp folder |
| `DB_NAME` | SQLite file |
| `AUDIO_BITRATE` | MP3 bitrate (default 192) |

Priority: **`.env` → `settings.json` → defaults**

```bash
python downld.py auth
```

### 2. Yandex Music access

```bash
python downld.py auth
python downld.py auth ym-token
python downld.py auth ym-cookie
python downld.py auth test
```

#### OAuth token

1. [music.yandex.ru](https://music.yandex.ru) - sign in
2. DevTools → Application → Local Storage / Cookies
3. `python downld.py auth ym-token`

#### Cookie / Session_id

1. Copy `Session_id` from cookies
2. `python downld.py auth ym-cookie`
3. Paste the value, `Session_id=...` string, or Netscape `cookies.txt`

### 3. CLI

```bash
python downld.py cli search -q "molchat doma sudno"
python downld.py cli download -q "molchat doma sudno"
python downld.py cli download -q "molchat doma sudno" --index 2
python downld.py cli download -u "https://music.yandex.ru/album/123/track/456"
python downld.py cli download -q "artist track" -o ./my_music
```

### 4. Telegram bot

```bash
python downld.py auth bot-token
python downld.py bot
```

```env
ADMIN_IDS=123456789
CHANNEL_USERNAME=your_channel
CHANNEL_LINK=https://t.me/your_channel
```

Commands: `/start`, `/help`, `/has_edit`, `/admin`, `/stats`, `/clear`

## 📋 Commands

| Command | Description |
|---|---|
| `python downld.py bot` | Telegram bot |
| `python downld.py auth` | Setup |
| `python downld.py auth show` | Current settings |
| `python downld.py auth ym-token` | Yandex OAuth |
| `python downld.py auth ym-cookie` | Cookie / Session_id |
| `python downld.py auth bot-token` | Telegram token |
| `python downld.py auth test` | API check |
| `python downld.py cli search -q "..."` | Search |
| `python downld.py cli download -q "..."` | Download |
| `python downld.py cli download -u URL` | Download by URL |

After `pip install -e .`, the `yamfetch` command is available with the same subcommands.

## Structure

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

## Security

- Do not commit `.env` and `settings.json`
- Use only your own Yandex Music account
