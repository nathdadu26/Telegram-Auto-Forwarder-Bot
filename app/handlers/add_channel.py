import asyncio

from telethon.tl.types import PeerChannel

from .. import database as db
from ..utils import schedule_delete


async def handle_forward_add(bot, userbot, event):
    """If the message is forwarded from a channel, verify admin rights and
    save it as a target channel. Returns True if this message was a
    channel-forward (handled here, regardless of outcome), False otherwise."""
    fwd = event.message.forward
    if not (fwd and fwd.from_id and isinstance(fwd.from_id, PeerChannel)):
        return False

    channel_id = fwd.from_id.channel_id

    try:
        entity = await userbot.get_entity(PeerChannel(channel_id))
    except Exception:
        try:
            await userbot.get_dialogs()
            entity = await userbot.get_entity(PeerChannel(channel_id))
        except Exception:
            await event.reply(
                "Could not verify that channel. Make sure my userbot account is "
                "already an admin there, then forward the message again."
            )
            return True

    try:
        user_me = await userbot.get_me()
        perm = await userbot.get_permissions(entity, user_me)
        if not (perm.is_admin or perm.is_creator):
            await event.reply(
                f"My userbot account is not an admin in **{entity.title}**. "
                f"Please make it an admin there first, then forward the message again."
            )
            return True
    except Exception:
        await event.reply("Could not verify admin rights there.")
        return True

    await db.add_channel(entity.id, entity.title, "target")
    sent = await event.reply(f"✅ New channel **{entity.title}** added.")
    asyncio.create_task(schedule_delete(sent, 300))
    return True
