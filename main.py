from tgtg import TgtgClient
from json import load
import requests
import time
import os
import traceback
import json
import maya
import datetime
import inspect
import dateutil.parser
import discord
from discord.ext import commands, tasks

try:
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    # Load credentials from a file
    f = open(os.path.join(path, 'config.json'), mode='r+')
    config = load(f)
except FileNotFoundError:
    print("No files found for local credentials.")
    exit(1)
except:
    print("Unexpected error")
    print(traceback.format_exc())
    exit(1)

try:
    # Create the tgtg client with credentials
    tgtg_client = TgtgClient(
        access_token=config['tgtg']['access_token'],
        refresh_token=config['tgtg']['refresh_token'],
        user_id=config['tgtg']['user_id'],
        cookie=config['tgtg']['cookie'])
except KeyError:
    try:
        if 'tgtg' not in config:
            config['tgtg'] = {}
        if 'foodsi' not in config:
            config['foodsi'] = {}

        # Check if tgtg credentials exist or prompt for input
        if 'access_token' not in config['tgtg']:
            email = input("Type your TooGoodToGo email address: ")
            client = TgtgClient(email=email)
            tgtg_creds = client.get_credentials()
            print(tgtg_creds)
            config['tgtg'] = tgtg_creds

        # Check if foodsi credentials exist or prompt for input
        if 'email' not in config['foodsi']:
            email = input("Type your Foodsi email address: ")
            password = input("Type your Foodsi password: ")
            config['foodsi']['email'] = email
            config['foodsi']['password'] = password

        # Save the updated config to the file
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()

        tgtg_client = TgtgClient(
            access_token=config['tgtg']['access_token'],
            refresh_token=config['tgtg']['refresh_token'],
            user_id=config['tgtg']['user_id'],
            cookie=config['tgtg']['cookie']
        )
    except:
        print(traceback.format_exc())
        exit(1)
except:
    print("Unexpected error")
    print(traceback.format_exc())
    exit(1)

try:
    bot_token = config['discord']['token']
    channel_id = config['discord']['channel_id']
except KeyError:
    print("No Discord data in the config.json file.")
    exit(1)
except:
    print("Unexpected error")
    print(traceback.format_exc())
    exit(1)

try:
    f.close()
except:
    print(traceback.format_exc())
    exit(1)

# Init the favourites in stock list as a global variable
tgtg_in_stock = list()
foodsi_in_stock = list()


# Global variables to store Foodsi headers
foodsi_headers = {}


# Function to perform the Foodsi login and store headers
def foodsi_login():
    global foodsi_headers

    # Credentials
    auth_data = {
        'email': config['foodsi']['email'],
        'password': config['foodsi']['password']
    }

    # Logging into the Foodsi API and capturing headers
    login_response = requests.post('https://api.foodsi.pl/api/v2/auth/sign_in', data=auth_data)
    if login_response.status_code == 200:
        foodsi_headers = {
            'access-token': login_response.headers.get('access-token'),
            'client': login_response.headers.get('client'),
            'uid': login_response.headers.get('uid')
        }
    else:
        print("Foodsi API login error")


# Call the Foodsi login function to obtain headers
foodsi_login()


intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)


# Global flag to track if the channel has been cleared
channel_cleared = False


# Function to clear the channel
async def clear_channel(channel):
    global channel_cleared
    if not channel_cleared:
        await channel.purge(limit=None)  # Clear the channel
        channel_cleared = True


# Function to send a Discord message
async def send_discord_message(message):
    channel = bot.get_channel(int(channel_id))
    if channel:
        await channel.send(message)
    else:
        print(f"Channel with ID {channel_id} not found")


# Event handler for bot's readiness
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Sending messages on a channel with an ID: {channel_id}')
    refresh.start()
    await clear_channel(bot.get_channel(int(channel_id)))  # Clear the channel


@bot.event
async def on_disconnect():
    print('Bot disconnected')
    refresh.cancel()  # Cancel the refresh task when the bot disconnects


# Define a background task using the tasks extension
@tasks.loop(seconds=15)  # Run every 15 seconds
async def refresh():
    try:
        await toogoodtogo()
        await foodsi()
    except:
        print(traceback.format_exc())


def parse_tgtg_api(api_result):
    result = list()
    # Go through all stores, that are returned with the api
    for store in api_result:
        current_item = dict()
        current_item['id'] = store['item']['item_id']
        current_item['store_name'] = store['store']['store_name']
        current_item['items_available'] = store['items_available']
        if current_item['items_available'] == 0:
            result.append(current_item)
            continue
        current_item['address'] = store['store']['store_location']['address']['address_line']
        current_item['description'] = store['item']['description']
        current_item['category_picture'] = store['item']['cover_picture']['current_url']
        current_item['price_including_taxes'] = str(store['item']['price_including_taxes']['minor_units'])[:-(store['item']['price_including_taxes']['decimals'])] + "." + str(store['item']['price_including_taxes']['minor_units'])[-(store['item']['price_including_taxes']['decimals']):]+store['item']['price_including_taxes']['code']
        current_item['value_including_taxes'] = str(store['item']['value_including_taxes']['minor_units'])[:-(store['item']['value_including_taxes']['decimals'])] + "." + str(store['item']['value_including_taxes']['minor_units'])[-(store['item']['value_including_taxes']['decimals']):]+store['item']['value_including_taxes']['code']
        try:
            localPickupStart = datetime.datetime.strptime(store['pickup_interval']['start'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            localPickupEnd = datetime.datetime.strptime(store['pickup_interval']['end'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            current_item['pickup_start'] = maya.parse(localPickupStart).slang_date().capitalize() + " " + localPickupStart.strftime('%H:%M')
            current_item['pickup_end'] = maya.parse(localPickupEnd).slang_date().capitalize() + " " + localPickupEnd.strftime('%H:%M')
        except KeyError:
            current_item['pickup_start'] = None
            current_item['pickup_end'] = None
        except:  # sloppy TODO
            current_item['pickup_start'] = dateutil.parser.parse(store['pickup_interval']['start']).strftime('%H:%M')
            current_item['pickup_end'] = dateutil.parser.parse(store['pickup_interval']['end']).strftime('%H:%M')
        result.append(current_item)
    return result


async def toogoodtogo():
    # Get the global variable of items in stock
    global tgtg_in_stock

    # Get all favorite items
    api_response = tgtg_client.get_items(
        favorites_only=False,
        latitude=config['location']['lat'],
        longitude=config['location']['long'],
        radius=config['location']['range'],
        page_size=300
    )

    parsed_api = parse_tgtg_api(api_response)

    # Go through all favourite items and compare the stock
    for item in parsed_api:
        try:
            old_stock = [stock['items_available'] for stock in tgtg_in_stock if stock['id'] == item['id']][0]
        except IndexError:
            old_stock = 0
        try:
            item['msg_id'] = [stock['msg_id'] for stock in tgtg_in_stock if stock['id'] == item['id']][0]
        except:
            pass

        new_stock = item['items_available']

        # Check, if the stock has changed. Send a message if so.
        if new_stock != old_stock:
            if old_stock == 0 and new_stock > 0:
                message = f".\n.\n.\n.\n.\n"
                message += f"***TooGoodToGo - There are {new_stock} new goodie bags at [{item['store_name']}]***\n"
                if item['address']:
                    message += f"Address: {item['address']}\n"
                if item['description']:
                    message += f"{item['description']}\n"
                if item['price_including_taxes'] and item['value_including_taxes']:
                    message += f"Price Before: {item['value_including_taxes']}\n"
                    message += f"Price After: {item['price_including_taxes']}\n"
                if item['pickup_start'] and item['pickup_end']:
                    message += f"Pickup Time: {item['pickup_start']} - {item['pickup_end']}\n"
                if item['category_picture']:
                    message += f"{item['category_picture']}\n"
                await send_discord_message(message)
            elif old_stock > new_stock != 0:
                # Decrease from {old_stock} to {new_stock}
                pass
            elif old_stock > new_stock == 0:
                # Sold out TODO
                pass
            else:
                message = f".\n.\n.\n.\n.\n"
                message += f"***TooGoodToGo - There was a change of number of goodie bags in stock from {old_stock} to {new_stock} at [{item['store_name']}]***"
                await send_discord_message(message)

    # Reset the global information with the newest fetch
    tgtg_in_stock = parsed_api

    # Print out some maintenance info in the terminal
    print(f"TGTG: API run at {time.ctime(time.time())} successful.")


def parse_foodsi_api(api_result):
    new_api_result = list()

    # Go through all favorites linked to the account,that are returned with the api
    for restaurant in api_result['data']:
        current_item = restaurant
        current_item['opened_at'] = dateutil.parser.parse(restaurant['package_day']['collection_day']['opened_at']).strftime('%H:%M')
        current_item['closed_at'] = dateutil.parser.parse(restaurant['package_day']['collection_day']['closed_at']).strftime('%H:%M')
        if restaurant['package_day']['meals_left'] is None:
            current_item['package_day']['meals_left'] = 0
            new_api_result.append(current_item)
            continue
        new_api_result.append(current_item)

    return new_api_result


async def foodsi():
    if not foodsi_headers:
        print("Foodsi headers not available.")
        return

    # Define the headers to include in requests
    headers = {
        'Content-type': 'application/json',
        'system-version': 'android_3.0.0',
        'user-agent': 'okhttp/3.12.0',
        **foodsi_headers  # Include the stored headers here
    }

    items = list()
    page = 1
    totalpages = 1

    while page <= totalpages:
        req_json = {
            "page": page,
            "per_page": 15,
            "distance": {
                "lat": config['location']['lat'],
                "lng": config['location']['long'],
                "range": config['location']['range'] * 1000
            },
            "hide_unavailable": False,
            "food_type": [],
            "collection_time": {
                "from": "00:00:00",
                "to": "23:59:59"
            }
        }

        # Add the headers to the request
        foodsi_api = requests.post('https://api.foodsi.pl/api/v2/restaurants',
                                   headers=headers,
                                   data=json.dumps(req_json))
        if foodsi_api.status_code == 200:
            items += parse_foodsi_api(foodsi_api.json())
            totalpages = foodsi_api.json()['total_pages']
            page += 1
        else:
            print("Foodsi API request error")

    # Get the global variable of items in stock
    global foodsi_in_stock

    # Go through all favourite items and compare the stock
    for item in items:
        try:
            old_stock = [stock['package_day']['meals_left'] for stock in foodsi_in_stock if stock['id'] == item['id']][0]
        except IndexError:
            old_stock = 0
        try:
            item['msg_id'] = [stock['msg_id'] for stock in foodsi_in_stock if stock['id'] == item['id']][0]
        except:
            pass

        new_stock = item['package_day']['meals_left']

        # Check, if the stock has changed. Send a message if so.
        if new_stock != old_stock:
            if old_stock == 0 and new_stock > 0:
                message = f".\n.\n.\n.\n.\n"
                message += f"***Foodsi - There are {new_stock} new goodie bags at [{item['name']}]***\n"
                if item['address']:
                    message += f"Address: {item['address']}\n"
                if item['meal']['description']:
                    message += f"{item['meal']['description']}\n"
                if item['meal']['original_price'] and item['meal']['price']:
                    message += f"Price Before: {item['meal']['original_price']}PLN\n"
                    message += f"Price After: {item['meal']['price']}PLN\n"
                if item['opened_at'] and item['closed_at']:
                    message += f"Pickup Time: {item['opened_at']} - {item['closed_at']}\n"
                if item['logo']['url']:
                    message += f"{item['logo']['url']}\n"
                await send_discord_message(message)
            elif old_stock > new_stock != 0:
                # Decrease from {old_stock} to {new_stock}
                pass
            elif old_stock > new_stock == 0:
                # Sold out TODO
                pass
            else:
                message = f".\n.\n.\n.\n.\n"
                message += f"***Foodsi - There was a change of number of goodie bags in stock from {old_stock} to {new_stock} at [{item['name']}]***"
                await send_discord_message(message)

    # Reset the global information with the newest fetch
    foodsi_in_stock = items

    # Print out some maintenance info in the terminal
    print(f"Foodsi: API run at {time.ctime(time.time())} successful.")


print("The bot script has started successfully. The bot checks every 15 seconds, if there is something new at TooGoodToGo or Foodsi. ")

bot.run(bot_token)
