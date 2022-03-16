# bot.py
import os
from urllib.request import urlopen
import discord
from discord.ext import commands
import json
import requests
import asyncio
import acc1puri
import acc2puri

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ACC1 = os.getenv('ACCOUNTSATU')
ACC2 = os.getenv('ACCOUNTDUA')
# client = discord.Client()
stet = True

client = commands.Bot(command_prefix='*', description="ewe")

@client.command()
async def asd(ctx):
    await ctx.send('pong')

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
        # if(a['stamina'] <= 90):
        #     acc1puri.Purification().run()
        if(b['stamina'] <= 60):
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= b['name'] + ' : on Purification'))
            acc2puri.Purification().run()
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= b['name'] + ' : ' + str(b['stamina']) + ' AP'))
        print('AP CHANGED 1')
        await asyncio.sleep(20)
        # total = acc2puri.Purification().getEvent()
        # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= b['name'] + ' : ' + str(total) + ' Medal'))
        # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= b['name'] + ' : on Story'))
        # print('AP CHANGED 2')
        # await asyncio.sleep(20)
        # if(total > 470000):
        #     channel = client.get_channel(947358313065111573)
        #     await channel.send('Farming Complete ' + str(total) + ' Medal Total')
        #     await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= b['name'] + ' : Done Farming'))
        #     break


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Your mom"))
    print(f'{client.user} has connected to Discord!')
    # client.loop.create_task(status_task())
client.run(TOKEN)
