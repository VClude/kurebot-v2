from config import APP_VERSION, UUID_PAYMENT, SESSION_ID, USER_ID, PRIV_KEY, AES_KEY
from SINoAPI import API
import json, base64, zlib, msgpack
from quests_deserializer import QuestSystemScheduleInfo
import simplejson
import socketio
import asyncio

def decompress(string: str):
    while '\/' in string:
        string = string.replace('\/', '/')

    decoded = base64.b64decode(string)
    decompressed = zlib.decompress(decoded)
    payload = msgpack.unpackb(decompressed)
    return payload

def handle_response(data: str):
    s = json.loads(data)
    d = decompress(s['payload'])
    return QuestSystemScheduleInfo(d)

class SocketManager():
    global api
    api = API(USER_ID, APP_VERSION, UUID_PAYMENT, PRIV_KEY, SESSION_ID)

    def __init__(self, data: RoomData) -> None:
        self.status = True
        self.url = 'https://reflector3-sinoalice-us.pokelabo.jp/'
        self.room_data = data
        self.sio = socketio.AsyncClient()

    def get_questWaveMstId(self, payload: dict):
        try:
            return payload['payload']['questData']['currentQuestWaveMstId']
        except KeyError:
            exit(payload)

    async def call_backs(self):

        @self.sio.event(namespace='/march')
        async def connect():
            log_info(f"Initialized Quest #{self.room_data.room_id}.")
            await self.sio.emit(2, "room_join", self.room_data.room_join(), namespace='/march')
            r = api.POST__api_quest_battle_get_info()
            api.POST__api_quest_battle_change_ai_mode(isAi=1)
            questWaveMstId = self.get_questWaveMstId(r)
            api.POST__api_quest_battle_wave_start(questWaveMstId)

        @self.sio.event(namespace='/march')
        async def quest_system_schedule_info(data):
            data = handle_response(data)
            enemiesHp = [x.hp for x in data.historyInfluenceData.members if x.guildDataId != 1]
            questData = data.historyInfluenceData.questData

            if questData.result == 1:
                await asyncio.sleep(1)
                # api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
                r = api.POST__api_quest_battle_finalize_stage_for_user()
                if r['payload']['success'] != True:
                    print(r)
                await self.sio.disconnect()
                return

            if all(x == 0 for x in enemiesHp):
                log_info("Cleared wave.")
                api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
                r = api.POST__api_quest_battle_get_info()
                questWaveMstId = self.get_questWaveMstId(r)
                api.POST__api_quest_battle_wave_start(questWaveMstId)

class Curry():
    def __init__(self):
        self.socket = SocketManager(USER_ID, APP_VERSION, UUID_PAYMENT, PRIV_KEY, SESSION_ID)

    def run(self):
        # remaining = 1
        # while remaining <= 20:
        #     res = self.api.POST__api_guild_get_event_data()
        #     print(remaining)
        #     df = open("event.json", "w")
        #     df.write(json.dumps(res))
        #     df.close()
        #     remaining += 1

        res = self.api.POST__api_gvg_out_battle_get_top()
        print("succ")
        df = open("get_top.json", "w")
        df.write(simplejson.dumps(res, indent=4, sort_keys=True))
        df.close()

        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(SocketManager.call_backs())
        # loop.close()

Curry().run()