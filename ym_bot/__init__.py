__all__ = ['Application']


def __getattr__(name):
    if name == 'Application':
        from ym_bot.application import Application
        return Application
    raise AttributeError(name)
