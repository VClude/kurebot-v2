from SINoAPI import API
import json, base64, zlib, msgpack
from quests_deserializer import QuestSystemScheduleInfo
import simplejson
import socketio
import asyncio
import datetime
import time
import aiomysql
from configkuresalt import APP_VERSION, UUID_PAYMENT, SESSION_ID, USER_ID, PRIV_KEY, AES_KEY
from discord import Webhook, AsyncWebhookAdapter, Embed, RequestsWebhookAdapter
import aiohttp

first = True
second = True
class Spgod():
    def __init__(self):
        self.api = API(USER_ID, APP_VERSION, UUID_PAYMENT, PRIV_KEY, SESSION_ID) # kure
    def run(self):
        res = self.api.POST__api_gvg_sp(100) #kure sp
        df = open("GETSP.json", "w")
        a = simplejson.dumps(res, indent=4, sort_keys=True)
        b = json.loads(a)
        df.write(a)
        df.close()
        return b

# Curry().run()

async def starting():
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url('https://discord.com/api/webhooks/951814101171064872/-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=AsyncWebhookAdapter(session))
        e = Embed(title="Auto-SP", description="Starting Saltellia Auto-SP")
        await webhook.send(embed=e)

def ending():
    webhook = Webhook.partial(951814101171064872, '-y2Z8gZNba-flX3PNTQgxjKT6WxG22fPaTcAAWLhYSfKlKChZtmx0uoGlSeVyOwv2UyR', adapter=RequestsWebhookAdapter())
    e = Embed(title="Auto-SP", description="Terminating Saltellia Auto-SP")
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
            print('SP-ING')
            Spgod().run()
            await asyncio.sleep(15)
        else:
            first = True
            print('waiting')
            await asyncio.sleep(2)
            

loop = asyncio.get_event_loop()
task = loop.create_task(wow())

try:
    loop.run_until_complete(task)
except KeyboardInterrupt:
    ending()
