class SocketManager():
    global api

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