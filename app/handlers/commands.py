from telethon import events

from .. import database as db
from ..utils import admin_only


def register(bot, userbot):

    @bot.on(events.NewMessage(pattern="/start"))
    @admin_only
    async def start_handler(event):
        text = (
            "**Telegram Auto-Forwarder Bot**\n\n"
            "I copy video files from any channel or group into your target channels, "
            "without the 'Forwarded from' tag and without captions.\n\n"
            "**How to use:**\n"
            "1. **Add a target channel:** make my userbot account an admin in that "
            "channel, send any message there, then forward that message to me here — "
            "I'll verify and save it.\n"
            "2. **Copy from a source:** send me any channel/group link (public or "
            "private invite link). I'll join it, copy every existing video into your "
            "target channels, and automatically re-check it once a day for new videos.\n"
            "3. **Copy to main channel:** send me any file (photo, video, document, etc.) "
            "directly and I'll copy it into your main channel.\n\n"
            "Multiple links are processed one at a time, in the order you send them.\n\n"
            "**Commands:**\n"
            "/start - Show this message\n"
            "/all_channels - List all channels with file counts\n"
        )
        await event.reply(text)

    @bot.on(events.NewMessage(pattern="/all_channels"))
    @admin_only
    async def all_channels_handler(event):
        channels = await db.get_all_channels()
        if not channels:
            await event.reply("No channels added yet. Forward a message from a channel to add it.")
            return
        lines = ["**All Channels:**\n"]
        for ch in channels:
            tag = "📌 Main" if ch["type"] == "main" else "🎯 Target"
            lines.append(f"{tag} — {ch['title']} — {ch['file_count']} files")
        await event.reply("\n".join(lines))
