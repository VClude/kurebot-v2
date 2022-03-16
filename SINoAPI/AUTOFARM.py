from config import APP_VERSION, UUID_PAYMENT, SESSION_ID, USER_ID, PRIV_KEY, AES_KEY
from SINoAPI import API
import simplejson
import socketio
import asyncio
import engineio

class Curry():
    def __init__(self):
        self.api = API(USER_ID, APP_VERSION, UUID_PAYMENT, PRIV_KEY, SESSION_ID)
        self.status = True
        self.url = 'https://reflector3-sinoalice-us.pokelabo.jp/'
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)

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
            r = self.api.POST__api_quest_battle_get_info()
            self.api.POST__api_quest_battle_change_ai_mode(isAi=1)
            questWaveMstId = self.get_questWaveMstId(r)
            self.api.POST__api_quest_battle_wave_start(questWaveMstId)
        @self.sio.event(namespace='/march')
        async def quest_system_schedule_info(data):
            data = handle_response(data)
            enemiesHp = [x.hp for x in data.historyInfluenceData.members if x.guildDataId != 1]
            questData = data.historyInfluenceData.questData

            if questData.result == 1:
                await asyncio.sleep(1)
                # api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
                r = self.api.POST__api_quest_battle_finalize_stage_for_user()
                if r['payload']['success'] != True:
                    print(r)
                await self.sio.disconnect()
                return

            if all(x == 0 for x in enemiesHp):
                log_info("Cleared wave.")
                self.api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
                r = self.api.POST__api_quest_battle_get_info()
                questWaveMstId = self.get_questWaveMstId(r)
                self.api.POST__api_quest_battle_wave_start(questWaveMstId)

    # @self.sio.event(namespace='/march')
    # async def connect():
    #     init = self.api.POST__api_quest_battle_initialize_stage()
    #     log_info(f"Initialized Quest #{self.room_data.room_id}.")
    #     await self.sio.emit(2, "room_join", self.room_data.room_join(), namespace='/march')
    #     r = self.api.POST__api_quest_battle_get_info()
    #     self.api.POST__api_quest_battle_change_ai_mode(isAi=1)
    #     questWaveMstId = self.get_questWaveMstId(r)
    #     self.api.POST__api_quest_battle_wave_start(questWaveMstId)

    # @self.sio.event(namespace='/march')
    # async def quest_system_schedule_info(data):
    #     data = handle_response(data)
    #     enemiesHp = [x.hp for x in data.historyInfluenceData.members if x.guildDataId != 1]
    #     questData = data.historyInfluenceData.questData

    #     if questData.result == 1:
    #         await asyncio.sleep(1)
    #         # api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
    #         r = api.POST__api_quest_battle_finalize_stage_for_user()
    #         if r['payload']['success'] != True:
    #             print(r)
    #         await self.sio.disconnect()
    #         return

    #     if all(x == 0 for x in enemiesHp):
    #         log_info("Cleared wave.")
    #         api.POST__api_quest_battle_wave_clear(questData.currentQuestWaveMstId)
    #         r = api.POST__api_quest_battle_get_info()
    #         questWaveMstId = self.get_questWaveMstId(r)
    #         api.POST__api_quest_battle_wave_start(questWaveMstId)
    
    async def run(self):
        res = self.api.POST__api_quest_battle_initialize_stage()
        df = open("DUMB.json", "w")
        df.write(simplejson.dumps(res, indent=4, sort_keys=True))
        df.close()
        await self.call_backs()


asyncio.run(Curry().call_backs(connect))