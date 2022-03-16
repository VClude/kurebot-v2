from configkuresalt import APP_VERSION, UUID_PAYMENT, SESSION_ID, USER_ID, PRIV_KEY, AES_KEY
from SINoAPI import API
import json, base64, zlib, msgpack
from quests_deserializer import QuestSystemScheduleInfo
import simplejson
import socketio
import asyncio
import time


class Curry():
    def __init__(self):
        self.api = API(USER_ID, APP_VERSION, UUID_PAYMENT, PRIV_KEY, SESSION_ID)

    def run(self):
        # remaining = 1
        # while remaining <= 20:
        #     res = self.api.POST__api_guild_get_event_data()
        #     print(remaining)
        #     df = open("event.json", "w")
        #     df.write(json.dumps(res))
        #     df.close()
        #     remaining += 1

        res = self.api.POST__api_gvg_sp()

        df = open("GETSP.json", "a")
        # df.write(simplejson.dumps(res, indent=4, sort_keys=True))
        df.write(simplejson.dumps(res, indent=4, sort_keys=True))
        df.close()

        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(SocketManager.call_backs())
        # loop.close()

Curry().run()