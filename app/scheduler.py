import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, database as db
from .queue import job_queue

TZ = ZoneInfo(config.TIMEZONE)


def seconds_until_next_midnight() -> float:
    now = datetime.now(TZ)
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (nxt - now).total_seconds()


async def daily_rescan_scheduler():
    while True:
        await asyncio.sleep(seconds_until_next_midnight())
        sources = await db.get_all_sources()
        for source in sources:
            await job_queue.put(("rescan", source))
