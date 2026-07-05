# Telegram Auto-Forwarder Bot

Copies video files from any channel/group (public or private) into your target
channels — without the "Forwarded from" tag and without captions — with
MongoDB-based duplicate detection, per-channel file limits, and a daily
automatic rescan for new videos.

## Folder structure

```
tg-forwarder-bot/
├── main.py                  # entry point - starts both clients + background jobs
├── app/
│   ├── config.py             # env vars
│   ├── database.py           # MongoDB (motor)
│   ├── utils.py               # video detection, progress bar, channel resolution
│   ├── queue.py               # serial job queue (links processed one at a time)
│   ├── scheduler.py           # daily midnight rescan scheduler
│   └── handlers/
│       ├── commands.py       # /start, /all_channels
│       ├── add_channel.py    # verifies + saves a target channel from a forward
│       ├── media.py          # direct media (any type) -> main channel
│       ├── scan.py           # link -> initial scan + copy, and daily rescan
│       └── router.py         # dispatches incoming messages
├── generate_session.py
├── requirements.txt
├── .env.example
├── Procfile
└── README.md
```

## Important: two Telegram clients working together

Telegram's Bot API bots (made via BotFather) **cannot join a channel/group via
an invite link** on their own — only a real user account can. So this project
runs two clients in the same process:

- **Bot** (`BOT_TOKEN`, from BotFather) — this is what you actually chat with:
  `/start`, `/all_channels`, forwarding messages to add channels, sending
  links, sending media. It must be an **admin of `MAIN_CHANNEL`**.
- **Userbot** (`SESSION_STRING`, a real account) — runs silently in the
  background. It joins source channels/groups from the links you send, scans
  them, and copies videos into your target channels. It must be an **admin of
  every target channel** you add.

Since the userbot performs bulk automated actions, be mindful of Telegram's
automation/ToS limits, and only forward content you have the right to
redistribute.

## 1. Create the Bot (BotFather)

Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token into
`BOT_TOKEN`. Add this bot as **admin** in your `MAIN_CHANNEL`.

## 2. Get API credentials (for both clients)

1. Go to https://my.telegram.org → **API development tools**
2. Create an app, copy `api_id` and `api_hash` — used by both the bot and the
   userbot

## 3. Generate a session string for the userbot (run locally, once)

```bash
pip install telethon
python generate_session.py
```

Log in with the phone number of the account you want to use as the userbot.
Copy the printed `SESSION_STRING` — you'll set it as an env var on Railway.

## 4. Set up MongoDB

Create a free cluster on MongoDB Atlas and get your connection string for
`MONGO_URI`.

## 5. Environment variables

Copy `.env.example` → `.env` (for local testing) or set these directly in
Railway's **Variables** tab:

| Variable | Description |
|---|---|
| `API_ID` / `API_HASH` | From my.telegram.org |
| `BOT_TOKEN` | From @BotFather — this is the bot you chat with |
| `SESSION_STRING` | From `generate_session.py` — the userbot account |
| `MONGO_URI` / `DB_NAME` | MongoDB connection |
| `MAIN_CHANNEL` | Channel ID (e.g. `-100...`) where directly-sent media is copied |
| `ADMIN_IDS` | Comma-separated Telegram user IDs allowed to control the bot |
| `MAX_FILES_PER_CHANNEL` | Default `2000` |
| `COPY_DELAY_SECONDS` | Default `10` |
| `TIMEZONE` | Default `Asia/Kolkata` — used for the daily midnight rescan |

## 6. Deploy on Railway

1. Push this folder to a GitHub repo
2. Railway → New Project → Deploy from GitHub repo
3. Add the environment variables above in **Variables**
4. Railway will use `Procfile` (`worker: python main.py`) to start the bot
5. Check **Deploy Logs** for `Bot is running...`

## Usage

### Add a target channel

1. Create/open the channel, make the **userbot account** an admin there
2. Send any message inside that channel
3. Forward that message to the bot (in your DM with it)

The bot reads the "forwarded from" info, verifies the userbot is admin there,
saves the channel, replies **"✅ New channel {name} added"**, and deletes that
confirmation after 5 minutes.

### Copy videos from a source channel/group

Send any channel/group **link** (public or private invite link) directly to
the bot. It will:

- Join the channel, count video files, show the total
- Copy them into your target channels (10s gap between copies, progress bar,
  auto-switches to the next target channel once one hits 2000 files)
- Remember the channel and the last message it saw
- **Automatically re-check it once a day** (at midnight, `TIMEZONE`) for any
  new videos posted since, copying only what's new

If you send **multiple links**, they're queued and processed **one at a
time** — the next one only starts once the current one finishes. The daily
rescans share the same queue, so they never run at the same time as a link
you send manually.

### Copy media to the main channel

Send **any file** (photo, video, document, etc.) directly to the bot in DM →
it's copied into `MAIN_CHANNEL`, the original message is deleted from your
chat, and the confirmation message is deleted automatically after 5 minutes.

### Other

- `/start` — show usage and commands
- `/all_channels` — list all channels (main + targets) with file counts

Duplicate files are detected via MongoDB — **separately for the main channel
and the target-channel pool**, so a file already in the main channel can
still be copied to a target channel, and vice versa.
