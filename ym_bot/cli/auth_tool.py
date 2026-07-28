import getpass

from ym_bot.config import Config
from ym_bot.settings import SettingsStore


class AuthTool:
    def __init__(self):
        self.store = SettingsStore.load()

    def apply(self):
        self.store.apply_to_config()

    def show(self):
        for line in self.store.status_lines():
            print(line)

    def set_ym_token(self, token=None):
        value = token or input('Yandex Music OAuth token: ').strip()
        if not value:
            print('Пустое значение, отмена')
            return 1
        self.store.set('ym_token', value)
        print(f'Сохранено: {SettingsStore.mask(value)}')
        return 0

    def set_bot_token(self, token=None):
        value = token or getpass.getpass('Telegram bot token: ').strip()
        if not value:
            print('Пустое значение, отмена')
            return 1
        self.store.set('bot_token', value)
        print(f'Сохранено: {SettingsStore.mask(value)}')
        return 0

    def set_vk_token(self, token=None):
        value = token or getpass.getpass('VK token (optional): ').strip()
        self.store.set('vk_token', value)
        print(f'Сохранено: {SettingsStore.mask(value)}')
        return 0

    def set_output_dir(self, path=None):
        value = path or input('Папка для CLI-скачиваний [downloads]: ').strip() or 'downloads'
        self.store.set('output_dir', value)
        print(f'output_dir = {value}')
        return 0

    def import_cookies(self, raw=None):
        print('Вставьте cookie и нажмите Enter дважды.')
        print('Поддерживается: Session_id=..., Netscape cookies.txt, или только значение Session_id')
        if raw:
            payload = raw
        else:
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if not line and lines:
                    break
                if line:
                    lines.append(line)
            payload = '\n'.join(lines)
        ok, message = self.store.import_cookies(payload)
        print(message)
        return 0 if ok else 1

    def test(self):
        from ym_bot.api.yandex import YandexMusicAPI

        self.apply()
        if not Config.YM_TOKEN:
            print('ym_token не задан. Запустите: python downld.py auth ym-token')
            return 1
        YandexMusicAPI.init()
        if not YandexMusicAPI.client:
            print('Не удалось подключиться к Яндекс.Музыке')
            return 1
        result = YandexMusicAPI.search('test', 'track')
        ok = bool(result and result.tracks and result.tracks.results)
        print('OK: поиск работает' if ok else 'Токен принят, но поиск вернул пустой результат')
        return 0 if ok else 1

    def menu(self):
        actions = {
            '1': ('Показать настройки', self.show),
            '2': ('Yandex OAuth token', lambda: self.set_ym_token()),
            '3': ('Yandex cookie / Session_id', lambda: self.import_cookies()),
            '4': ('Telegram bot token', lambda: self.set_bot_token()),
            '5': ('VK token', lambda: self.set_vk_token()),
            '6': ('Папка downloads', lambda: self.set_output_dir()),
            '7': ('Проверить Yandex', self.test),
        }
        print('=== Настройка yandex-music-download ===')
        for key, (label, _) in actions.items():
            print(f'{key}. {label}')
        print('0. Выход')
        choice = input('> ').strip()
        if choice == '0':
            return 0
        action = actions.get(choice)
        if not action:
            print('Неизвестный пункт')
            return 1
        return action[1]() or 0

    def run(self, args):
        if not args.command or args.command == 'menu':
            return self.menu()
        if args.command == 'show':
            self.show()
            return 0
        if args.command == 'ym-token':
            return self.set_ym_token(args.value)
        if args.command == 'ym-cookie':
            return self.import_cookies(args.value)
        if args.command == 'bot-token':
            return self.set_bot_token(args.value)
        if args.command == 'vk-token':
            return self.set_vk_token(args.value)
        if args.command == 'output':
            return self.set_output_dir(args.value)
        if args.command == 'test':
            return self.test()
        print(f'Неизвестная auth-команда: {args.command}')
        return 1
