import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel

from app import config, database as db
from app.handlers import register_all
from app.utils import parse_channel_id
from app.queue import worker
from app.scheduler import daily_rescan_scheduler

bot = TelegramClient(StringSession(), config.API_ID, config.API_HASH)
userbot = TelegramClient(StringSession(config.SESSION_STRING), config.API_ID, config.API_HASH)


async def main():
    await bot.start(bot_token=config.BOT_TOKEN)
    await userbot.start()

    bot_me = await bot.get_me()
    user_me = await userbot.get_me()
    print(f"Bot: @{bot_me.username} | Userbot: {user_me.first_name} ({user_me.id})")

    # The userbot's entity cache is empty on every fresh restart (it isn't
    # persisted in SESSION_STRING). Without this, sending files to a target
    # channel by its stored ID silently fails right after every redeploy.
    await userbot.get_dialogs()

    register_all(bot, userbot)

    if config.MAIN_CHANNEL:
        entity = None
        try:
            entity = await bot.get_entity(config.MAIN_CHANNEL)
        except Exception:
            try:
                await bot.get_dialogs()
                entity = await bot.get_entity(PeerChannel(parse_channel_id(str(config.MAIN_CHANNEL))))
            except Exception as e2:
                print(f"Warning: could not resolve MAIN_CHANNEL: {e2}")
        if entity:
            await db.add_channel(entity.id, entity.title, "main")

    asyncio.create_task(worker(bot, userbot))
    asyncio.create_task(daily_rescan_scheduler())

    print("Bot is running...")
    await asyncio.gather(bot.run_until_disconnected(), userbot.run_until_disconnected())


if __name__ == "__main__":
    bot.loop.run_until_complete(main())
