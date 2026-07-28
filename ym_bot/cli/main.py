import argparse
import sys

from ym_bot.cli.auth_tool import AuthTool


def build_parser():
    parser = argparse.ArgumentParser(
        prog='yamfetch',
        description='yamfetch — Yandex Music bot and CLI',
    )
    sub = parser.add_subparsers(dest='mode')

    sub.add_parser('bot', help='Запустить Telegram-бота')

    auth = sub.add_parser('auth', help='Настройка токенов и cookie')
    auth.add_argument(
        'command',
        nargs='?',
        choices=['menu', 'show', 'ym-token', 'ym-cookie', 'bot-token', 'vk-token', 'output', 'test'],
        default='menu',
    )
    auth.add_argument('value', nargs='?', help='Значение для non-interactive режима')

    cli = sub.add_parser('cli', help='Скачивание из терминала')
    cli_sub = cli.add_subparsers(dest='action')
    cli_search = cli_sub.add_parser('search', help='Поиск треков')
    cli_search.add_argument('--query', '-q', required=True)
    cli_search.add_argument('--limit', '-n', type=int, default=10)
    cli_search.add_argument('--output', '-o', default=None)
    cli_download = cli_sub.add_parser('download', help='Скачать трек/альбом/плейлист')
    cli_download.add_argument('--url', '-u', default=None, help='Ссылка Яндекс.Музыки')
    cli_download.add_argument('--query', '-q', default=None, help='Поисковый запрос')
    cli_download.add_argument('--index', type=int, default=0, help='Номер трека в выдаче (0-based)')
    cli_download.add_argument('--output', '-o', default=None, help='Папка сохранения')

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        argv = ['bot']
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == 'bot':
        from ym_bot.application import Application

        Application.run()
        return 0
    if args.mode == 'auth':
        return AuthTool().run(args)
    if args.mode == 'cli':
        from ym_bot.cli.runner import CliRunner

        if not args.action:
            print('Используйте: cli search или cli download')
            return 1
        return CliRunner().run(args)
    parser.print_help()
    return 1
