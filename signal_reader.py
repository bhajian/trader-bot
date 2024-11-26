from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.tl.types import PeerChannel
from openai import OpenAI
from datetime import datetime
import requests
import json
import os


login_url = "https://www.k2xch.com/prod-api/user/login"
trial_url = "https://www.k2xch.com/prod-api/user/trialMode"
spot_url = "https://www.k2xch.com/prod-api/symbol/spot"

today = datetime.today()
formatted_date = today.strftime("%Y-%m-%d")
# Replace these with your API credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Replace with your OpenAI API key
MODEL=os.getenv("MODEL")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
openaiClient = OpenAI(api_key=OPENAI_API_KEY)

SOURCE_GROUP = os.getenv("SOURCE_GROUP")
TARGET_USER = os.getenv("TARGET_USER")
SPECIFIC_USER = os.getenv("SPECIFIC_USER")

# Initialize the Telegram client
client = TelegramClient('bot_session', API_ID, API_HASH)

def prompt_openai(prompt_text):
    try:
        completion = openaiClient.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text},
            ]
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:  # Handle any API or runtime errors
        return f"An error occurred: {e}"


async def request(params):
    try:
        if params["type"] == "GET":  # Access dictionary keys using []
            response = requests.get(params["url"], headers=params["headers"])
            print("Response:", response.json())
            return response.json()
        elif params["type"] == "POST":
            print(params["url"])
            print(params["data"])
            response = requests.post(params["url"], data=json.dumps(params["data"], indent=4), headers=params["headers"])
            print("Response:", response.json())
            return response.json()
    except requests.exceptions.Timeout:
        print("The request timed out.")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


@client.on(events.NewMessage)
async def handler(event):
    print("HERE")
    # chat = await event.get_chat()
    sender = await event.get_sender()
    # entity = await client.get_entity(SOURCE_GROUP)
    # print(f"Successfully resolved entity: {entity}")
    print(f"Message forwarded: {event.message.text}")
    print(sender.username)

    if event.sender and event.sender.username == SPECIFIC_USER:
        # Forward the message to the target user
        response = prompt_openai("The following text after :: as the input contains a message from a telegram channel, analyze it and if " 
            +" the message contains a signal for trading that includes direction and the time is given in AST (Arabia Standard Time) with (hh:mm) format in the input."
            +" AST is (GMT+3). EST is (GMT-5). IRST is (GMT+3:30). "
            +" If the message contains a signal then convert it to JSON with the following conditions and field:" 
            +" Toronto_time: input time converted to EST (Estern Time Zone) for Toronto in (hh:mm) format, Tehran_time: input time converted to IRST (Iran Standard Time) for Tehran, "
            + ", type (BTC/USDT), direction (UP or DOWN), stage which is value [1-6] given in the input, account_portion: the percent of the account " 
            +", time type is a integer value given in the input. If it doesn't contain information about signal only return 'NONE'. Only return 'NONE' or json values extracted from input. " 
            +" The Json contains these fields (Toronto_time, Tehran_time, type, direction, time_type, stage, account_portion). don't include extra words in your json string, it should be convertable in python to dictionary. :: " + event.message.text)
        if(response != "NONE"):
            await client.send_message(TARGET_USER, event.message.text)
            await client.send_message(TARGET_USER, response)
            response = clean_gpt_response(response)
            await trade(response)
        else:
            print (response)

def clean_gpt_response(chatgpt_string):
    cleaned_string = chatgpt_string.replace("```", "").replace("json", "").strip()
    print(cleaned_string)
    try:
        data = json.loads(cleaned_string)
        return data
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)


async def trade(signal):
    login_obj = {
        "url": login_url,
        "headers": {
            "Content-Type": "application/json"
        },
        "data": {
            "username": "m.gharehaghaj@gmail.com",
            "password": "MahsaBehnam123",
            "operatingSystem": "Mac OS",
            "browser": "Chrome"
        },
        "type": "POST"
    }
    login_res = await request(login_obj)
    trial_obj = {
        "url": trial_url,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": login_res["data"]["token"]
        },
        "type": "GET"
    }
    trial_res = await request(trial_obj)
    time = signal["Toronto_time"]
    date_time_str = f"{formatted_date} {time}"
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
    epoch_time = int(date_time_obj.timestamp()) * 1000
    print (epoch_time)
    trial_obj = {
        "url": spot_url,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": trial_res["data"]["token"]
        },
        "data": {
            "symbol": "1",
            "tradeType": signal["direction"],
            "seconds": "60",
            "amount": "10.36",
            "expectTime": epoch_time
        },
        "type": "POST"
    }
    trial_res = await request(trial_obj)



async def main():
    await client.start(bot_token=BOT_TOKEN)
 
    me = await client.get_me()
    print(f"Logged in as {me.username}")
    print("Bot is running...")
    await client.run_until_disconnected()
    

if __name__ == '__main__':

    with client:
        client.loop.run_until_complete(main())
