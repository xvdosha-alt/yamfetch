import asyncio

from ym_bot.config import Config
from ym_bot.services.local_download import LocalDownloadService


class CliRunner:
    def __init__(self):
        self.downloader = LocalDownloadService()

    @staticmethod
    def bootstrap():
        from ym_bot.api.vk import VKMusicAPI
        from ym_bot.api.yandex import YandexMusicAPI

        Config.bootstrap()
        YandexMusicAPI.init()
        if not YandexMusicAPI.client:
            print('Ошибка: Yandex Music API не инициализирован')
            print('Настройте токен: python downld.py auth ym-token')
            print('Или cookie:     python downld.py auth ym-cookie')
            return False
        if Config.VK_TOKEN:
            asyncio.run(VKMusicAPI.auth())
        return True

    def cmd_search(self, args):
        self.downloader = LocalDownloadService(args.output)
        self.downloader.print_search(args.query, limit=args.limit)
        return 0

    def cmd_download(self, args):
        self.downloader = LocalDownloadService(args.output)
        try:
            if args.url:
                paths = self.downloader.download_url(args.url, args.output)
            elif args.query:
                path = self.downloader.download_query(args.query, args.output, index=args.index)
                paths = [path]
            else:
                print('Укажите --url или --query')
                return 1
        except RuntimeError as exc:
            print(f'Ошибка: {exc}')
            return 1
        print(f'Готово: {len(paths)} файл(ов)')
        for path in paths:
            print(path)
        return 0

    def run(self, args):
        if not self.bootstrap():
            return 1
        if args.action == 'search':
            if not args.query:
                print('Нужен --query')
                return 1
            return self.cmd_search(args)
        if args.action == 'download':
            if not args.url and not args.query:
                print('Нужен --url или --query')
                return 1
            return self.cmd_download(args)
        print(f'Неизвестная cli-команда: {args.action}')
        return 1
