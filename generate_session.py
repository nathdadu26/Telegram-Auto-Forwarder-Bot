"""
Run this ONCE on your own computer (not on Railway) to generate a SESSION_STRING.
You will be asked to log in with the phone number of the account that will run
the bot (this account must be an admin in your target/main channels).
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("Enter API_ID: "))
api_hash = input("Enter API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as tg_client:
    print("\nYour SESSION_STRING (copy this into Railway's SESSION_STRING variable):\n")
    print(tg_client.session.save())
