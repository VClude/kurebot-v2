# bot.py
import os
from urllib.request import urlopen
import discord
import json
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ACC1 = os.getenv('ACCOUNTSATU')
ACC2 = os.getenv('ACCOUNTDUA')
client = discord.Client()


def getap():

    url = "http://xvc.cleverapps.io/getuser2/"
    response = requests.get(url+ACC1).text
    response2 = requests.get(url+ACC2).text

    D1 = json.loads(response)
    D2 = json.loads(response2)

    AP1 = D1['payload']['userData']
    AP2 = D2['payload']['userData']

    return AP1, AP2


async def status_task():
    while True:
        a, b = getap()
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= a['name'] + ' : ' + str(a['stamina']) + ' AP | ' + b['name'] + ' : ' + str(b['stamina']) + ' AP'))
        await asyncio.sleep(60)
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= a['name'] + ' : ' + str(a['stamina']) + ' AP | ' + b['name'] + ' : ' + str(b['stamina']) + ' AP'))
        await asyncio.sleep(60)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Sino Accounts"))
    print(f'{client.user} has connected to Discord!')
    client.loop.create_task(status_task())
client.run(TOKEN)
