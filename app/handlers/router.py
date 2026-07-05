from telethon import events
from telethon.tl.types import MessageMediaWebPage

from ..utils import admin_only, LINK_RE
from ..queue import job_queue
from .media import handle_direct_media
from .add_channel import handle_forward_add


def register(bot, userbot):

    @bot.on(events.NewMessage())
    @admin_only
    async def message_router(event):
        if event.raw_text and event.raw_text.startswith("/"):
            return  # handled by commands.py

        if event.message.forward:
            handled = await handle_forward_add(bot, userbot, event)
            if handled:
                return

        if event.media and not isinstance(event.media, MessageMediaWebPage):
            await handle_direct_media(bot, event)
            return

        if event.raw_text and LINK_RE.search(event.raw_text):
            await job_queue.put(("link", event))
            await event.reply("🔗 Link received and queued — links are processed one at a time.")
