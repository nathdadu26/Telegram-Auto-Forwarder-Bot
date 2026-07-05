from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from . import config

_client = AsyncIOMotorClient(config.MONGO_URI)
db = _client[config.DB_NAME]

channels_col = db["channels"]
files_col = db["files"]
sources_col = db["sources"]


async def add_channel(chat_id: int, title: str, channel_type: str = "target"):
    """Insert a channel if it doesn't already exist. channel_type: 'target' or 'main'."""
    await channels_col.update_one(
        {"_id": chat_id},
        {
            "$set": {"title": title},
            "$setOnInsert": {
                "type": channel_type,
                "file_count": 0,
                "added_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )


async def channel_exists(chat_id: int) -> bool:
    return await channels_col.find_one({"_id": chat_id}) is not None


async def get_all_channels():
    return await channels_col.find().sort("added_at", 1).to_list(length=None)


async def get_available_target_channel():
    """Returns the oldest-added target channel that still has room (< MAX_FILES_PER_CHANNEL)."""
    return await channels_col.find_one(
        {"type": "target", "file_count": {"$lt": config.MAX_FILES_PER_CHANNEL}},
        sort=[("added_at", 1)],
    )


async def increment_file_count(chat_id: int, by: int = 1):
    await channels_col.update_one({"_id": chat_id}, {"$inc": {"file_count": by}})


async def is_duplicate(file_id: int, scope: str) -> bool:
    """scope is 'main' or 'target' — the two are tracked separately, so a file
    already copied to the main channel can still go to a target channel and
    vice versa."""
    if file_id is None:
        return False
    return await files_col.find_one({"_id": f"{scope}:{file_id}"}) is not None


async def save_file_record(file_id: int, source_chat_id: int, target_chat_id: int, scope: str):
    if file_id is None:
        return
    await files_col.update_one(
        {"_id": f"{scope}:{file_id}"},
        {
            "$setOnInsert": {
                "file_id": file_id,
                "scope": scope,
                "source_chat_id": source_chat_id,
                "target_chat_id": target_chat_id,
                "added_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


async def add_source(chat_id: int, title: str, link: str, last_message_id: int = 0):
    """Tracks a source channel that was scanned via a link, so it can be
    revisited during the daily rescan for new videos."""
    await sources_col.update_one(
        {"_id": chat_id},
        {
            "$set": {"title": title, "link": link},
            "$setOnInsert": {"added_at": datetime.utcnow()},
            "$max": {"last_message_id": last_message_id},
        },
        upsert=True,
    )


async def update_last_message_id(chat_id: int, message_id: int):
    await sources_col.update_one({"_id": chat_id}, {"$max": {"last_message_id": message_id}})


async def get_all_sources():
    return await sources_col.find().to_list(length=None)
