import asyncio
import traceback

from telethon.errors import FloodWaitError

from .. import config, database as db
from ..queue import wait_if_paused
from ..utils import LINK_RE, is_video, get_file_id, progress_bar, resolve_and_join, resolve_by_id


async def _copy_videos(userbot, status, entity, messages):
    """Copies a list of video messages into available target channels
    (10s gap, 2000-file rotation, duplicate-skipped). `status` (a message to
    edit with progress) may be None for silent/background runs."""
    total = len(messages)
    copied = 0
    duplicates = 0
    errors = 0

    for i, message in enumerate(messages, start=1):
        await wait_if_paused()

        file_id = get_file_id(message)
        if await db.is_duplicate(file_id, "target"):
            duplicates += 1
        else:
            target = await db.get_available_target_channel()
            if target is None:
                if status:
                    await status.edit(
                        f"⚠️ All target channels reached the {config.MAX_FILES_PER_CHANNEL}-file limit.\n"
                        f"Copied {copied}/{total} so far. Add a new target channel — "
                        f"I'll pick up the rest on the next run."
                    )
                return copied, duplicates, errors
            try:
                target_entity = await resolve_by_id(userbot, str(target["_id"]))
                if target_entity is None:
                    raise ValueError(f"Could not resolve target channel {target['_id']}")
                await userbot.send_file(target_entity, file=message.media, caption="")
                await db.save_file_record(file_id, entity.id, target["_id"], "target")
                await db.increment_file_count(target["_id"])
                copied += 1
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                errors += 1
                print(f"Copy error (message {message.id} -> {target['_id']}):")
                traceback.print_exc()

        if status and (i % 3 == 0 or i == total):
            bar = progress_bar(i, total)
            await status.edit(
                f"**{entity.title}**\n{bar} {i}/{total}\n"
                f"Copied: {copied} | Duplicate: {duplicates} | Errors: {errors}"
            )

        if i != total:
            await asyncio.sleep(config.COPY_DELAY_SECONDS)

    return copied, duplicates, errors


async def handle_channel_scan(bot, userbot, event):
    """Triggered when the admin sends a channel/group link. Joins it, copies
    every existing video, then remembers the channel + highest message ID
    seen so the daily rescan can pick up only new videos later."""
    link_match = LINK_RE.search(event.raw_text)
    link = link_match.group(0)

    status = await event.reply("🔍 Resolving and joining channel...")
    entity = await resolve_and_join(userbot, link)
    if entity is None:
        await status.edit("❌ Could not join/resolve that channel. Check the link.")
        return

    await status.edit(f"📡 Scanning **{entity.title}** for video files...")
    all_messages = []
    async for message in userbot.iter_messages(entity):
        all_messages.append(message)

    highest_id = max((m.id for m in all_messages), default=0)
    video_messages = [m for m in all_messages if is_video(m)]
    total = len(video_messages)

    if total == 0:
        await status.edit(f"No video files found in **{entity.title}**.")
        await db.add_source(entity.id, entity.title, link, highest_id)
        return

    await status.edit(f"📦 Found **{total}** video files in **{entity.title}**.\nStarting copy...")
    copied, duplicates, errors = await _copy_videos(userbot, status, entity, video_messages)

    await db.add_source(entity.id, entity.title, link, highest_id)
    await status.edit(
        f"✅ Done. Copied {copied}/{total} videos from **{entity.title}**.\n"
        f"Duplicate: {duplicates} | Errors: {errors}"
    )


async def handle_rescan(bot, userbot, source):
    """Runs once daily (queued at midnight) for every tracked source channel:
    fetches only messages newer than last_message_id, copies any new videos,
    and advances last_message_id."""
    channel_id = source["_id"]
    last_id = source.get("last_message_id", 0)
    link = source.get("link")

    entity = await resolve_by_id(userbot, str(channel_id))
    if entity is None and link:
        entity = await resolve_and_join(userbot, link)
    if entity is None:
        print(f"Rescan: could not resolve source {source.get('title')} ({channel_id})")
        return

    new_messages = []
    async for message in userbot.iter_messages(entity, min_id=last_id, reverse=True):
        new_messages.append(message)

    if not new_messages:
        return

    highest_id = max(m.id for m in new_messages)
    video_messages = [m for m in new_messages if is_video(m)]

    status = None
    if video_messages and config.ADMIN_IDS:
        try:
            status = await bot.send_message(
                config.ADMIN_IDS[0],
                f"🔄 Daily rescan: found {len(video_messages)} new video(s) in **{entity.title}**.",
            )
        except Exception:
            status = None

    if video_messages:
        copied, duplicates, errors = await _copy_videos(userbot, status, entity, video_messages)
        if status:
            await status.edit(
                f"✅ Rescan done for **{entity.title}**. Copied {copied}, "
                f"duplicate {duplicates}, errors {errors}."
            )

    await db.update_last_message_id(channel_id, highest_id)
