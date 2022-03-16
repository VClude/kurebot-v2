import os
from urllib.request import urlopen
from SINoAPI import API
import json, base64, zlib, msgpack
from quests_deserializer import QuestSystemScheduleInfo
import simplejson
import socketio
import asyncio
import datetime
import time
import aiomysql
from dotenv import load_dotenv
import discord
from discord import Webhook, AsyncWebhookAdapter, Embed, RequestsWebhookAdapter
import aiohttp
load_dotenv()

first = True
second = True
APP_VER = '27.1.0'
loop = asyncio.get_event_loop()
class Spgod():
    def __init__(self, userid, uuid, priv, sess):
        self.api = API(userid, APP_VER, uuid, priv, sess)

    def getStatus(self):

        res = self.api.POST__api_user_get_user_data()
        df = open("getuser.json", "a")
        df.write(simplejson.dumps(res, indent=4, sort_keys=True))
        df.close()
        a = simplejson.dumps(res, indent=4, sort_keys=True)
        b = json.loads(a)
        return b

    def doSP(self, val:int=50):
        res = self.api.POST__api_gvg_sp(val)
        a = simplejson.dumps(res, indent=4, sort_keys=True)
        b = json.loads(a)
        return b


# Curry().run()
async def get_user_active():
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("SELECT * from user where active and ts = 12")
    r = await cur.fetchall()
    await cur.close()
    conn.close()

    return r

async def starting():
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url('https://discord.com/api/webhooks/951814101171064872/-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=AsyncWebhookAdapter(session))
        e = Embed(title="Auto-SP", description="Starting TS 12 Auto-SP")
        await webhook.send(embed=e)

async def sendHook(user: str, val: int, valjadi: int):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url('https://discord.com/api/webhooks/951814101171064872/-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=AsyncWebhookAdapter(session))
        e = Embed(title="Auto-SP", description=user + " SP Recovered by " + str(val) + " | Current SP : " + str(valjadi))
        await webhook.send(embed=e)

def ending():
    webhook = Webhook.partial(951814101171064872, '-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=RequestsWebhookAdapter())
    e = Embed(title="Auto-SP", description="Terminating TS 12 Auto-SP")
    webhook.send(embed=e)

# async def sendSP():
#     async with aiohttp.ClientSession() as session:
#         webhook = Webhook.from_url('https://discord.com/api/webhooks/951814101171064872/-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=AsyncWebhookAdapter(session))
#         e = discord.Embed(title="Auto-SP", description="Starting Auto-SP")
#         await webhook.send(embed=e)

async def wow():
    global first
    while True:
        now = datetime.datetime.now()
        if now.hour == 20 and 0 <= now.minute <= 20:
            if first:
                print("only once")
                await starting()
                first = False
            ACC = await get_user_active()
            embed = discord.Embed(title="Status", description="SP Recovered", color=0xff00ff)
            for x in ACC:
                try:
                    dat = Spgod(x[4], x[2], x[5], x[3]).doSP(x[7])
                    b = dat["payload"]["gvgSp"]
                    print(x[1])
                    print(b)
                except:
                    print(x[1] + " Failed")
                await sendHook(x[1], x[7], b)
            
            await asyncio.sleep(15)
        else:
            first = True
            print('waiting')
            await asyncio.sleep(2)
            


task = loop.create_task(wow())

try:
    loop.run_until_complete(task)
except KeyboardInterrupt:
    ending()
