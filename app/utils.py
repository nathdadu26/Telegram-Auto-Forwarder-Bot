import asyncio
import re

from telethon.tl.types import (
    DocumentAttributeVideo,
    PeerChannel,
    ChatInviteAlready,
    ChatInvitePeek,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors import InviteHashExpiredError

from . import config

LINK_RE = re.compile(r"(?:https?://)?t\.me/(\+|joinchat/)?([A-Za-z0-9_-]+)")


def admin_only(func):
    async def wrapper(event):
        if event.sender_id not in config.ADMIN_IDS:
            return
        await func(event)
    return wrapper


def is_video(message) -> bool:
    if message.video:
        return True
    if message.document:
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeVideo):
                return True
        if message.document.mime_type and message.document.mime_type.startswith("video/"):
            return True
    return False


def get_file_id(message):
    if message.document:
        return message.document.id
    if message.photo:
        return message.photo.id
    return None


async def schedule_delete(message, delay=300):
    """Deletes a message after `delay` seconds (default 5 minutes)."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


def progress_bar(current, total, length=15) -> str:
    filled = int(length * current / total) if total else 0
    pct = int(current / total * 100) if total else 0
    return "[" + "█" * filled + "░" * (length - filled) + f"] {pct}%"


def parse_channel_id(raw: str) -> int:
    """Accepts -100xxxxxxxxxx (Bot-API style) or the plain channel id."""
    raw = raw.strip()
    if raw.startswith("-100"):
        return int(raw[4:])
    return int(raw)


async def resolve_by_id(client, raw_id: str):
    """Resolve a channel/group entity from its numeric ID.
    The account must already be a member (required anyway, since it must be admin)."""
    try:
        channel_id = parse_channel_id(raw_id)
    except ValueError:
        return None
    try:
        return await client.get_entity(PeerChannel(channel_id))
    except Exception:
        try:
            await client.get_dialogs()  # populate entity cache
            return await client.get_entity(PeerChannel(channel_id))
        except Exception:
            return None


async def resolve_and_join(client, link: str):
    """Used only for the link-based SOURCE-channel scanning workflow
    (joining a channel to read/copy its videos still needs a link)."""
    match = LINK_RE.search(link)
    if not match:
        return None
    prefix, value = match.groups()
    try:
        if prefix:  # private invite link
            invite = await client(CheckChatInviteRequest(value))
            if isinstance(invite, (ChatInviteAlready, ChatInvitePeek)):
                return invite.chat
            updates = await client(ImportChatInviteRequest(value))
            return updates.chats[0]
        else:  # public username
            entity = await client.get_entity(value)
            try:
                await client(JoinChannelRequest(entity))
            except Exception:
                pass
            return entity
    except InviteHashExpiredError:
        return None
    except Exception:
        return None
