from . import commands, router


def register_all(bot, userbot):
    commands.register(bot, userbot)
    router.register(bot, userbot)
