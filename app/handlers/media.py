import asyncio

from .. import config, database as db
from ..utils import get_file_id, schedule_delete


async def handle_direct_media(bot, event):
    file_id = get_file_id(event.message)
    if await db.is_duplicate(file_id, "main"):
        await event.reply("⚠️ This file already exists (duplicate). Skipped.")
        return
    await bot.send_file(config.MAIN_CHANNEL, file=event.message.media, caption="")
    await db.save_file_record(file_id, event.chat_id, config.MAIN_CHANNEL, "main")
    await db.increment_file_count(config.MAIN_CHANNEL)
    await event.delete()
    sent = await bot.send_message(event.chat_id, "✅ Copied to main channel and deleted here.")
    asyncio.create_task(schedule_delete(sent, 300))
