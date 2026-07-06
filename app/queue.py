import asyncio

job_queue = asyncio.Queue()

# Set = running normally. Cleared = paused — the worker won't start a new
# queued job, and any in-progress copy loop will pause between files too.
resume_event = asyncio.Event()
resume_event.set()


async def wait_if_paused():
    await resume_event.wait()


async def worker(bot, userbot):
    """Consumes jobs one at a time — a new link is never started before the
    previous one (or a scheduled rescan) has fully finished."""
    from .handlers.scan import handle_channel_scan, handle_rescan

    while True:
        kind, payload = await job_queue.get()
        await wait_if_paused()
        try:
            if kind == "link":
                await handle_channel_scan(bot, userbot, payload)
            elif kind == "rescan":
                await handle_rescan(bot, userbot, payload)
        except Exception as e:
            print(f"Job error ({kind}): {e}")
        finally:
            job_queue.task_done()
