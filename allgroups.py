from telethon import TelegramClient


client = TelegramClient("bot_session", API_ID, API_HASH)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    async for dialog in client.iter_dialogs():
        print(f"Name: {dialog.name}, ID: {dialog.id}, Entity: {dialog.entity}")

with client:
    client.loop.run_until_complete(main())
