import asyncio

job_queue = asyncio.Queue()


async def worker(bot, userbot):
    """Consumes jobs one at a time — a new link is never started before the
    previous one (or a scheduled rescan) has fully finished."""
    from .handlers.scan import handle_channel_scan, handle_rescan

    while True:
        kind, payload = await job_queue.get()
        try:
            if kind == "link":
                await handle_channel_scan(bot, userbot, payload)
            elif kind == "rescan":
                await handle_rescan(bot, userbot, payload)
        except Exception as e:
            print(f"Job error ({kind}): {e}")
        finally:
            job_queue.task_done()
