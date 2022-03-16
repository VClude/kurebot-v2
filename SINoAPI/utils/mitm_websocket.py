import mitmproxy.websocket, time, json, simplejson, zlib, msgpack, base64
from types import SimpleNamespace
from quests_deserializer import QuestSystemScheduleInfo
from mitmproxy import ctx, http
import re
import puri

# def decompress(string: bytes):
#     while '\/' in string:
#         string = string.replace('\/', '/')

#     # decoded = base64.b64decode(string)
#     # decompressed = zlib.decompress(decoded)
#     # payload = msgpack.unpackb(decompressed)
#     return string

def decompress(string: str):
    while '\/' in string:
        string = string.replace('\/', '/')

    decoded = base64.b64decode(string)
    decompressed = zlib.decompress(decoded)
    payload = msgpack.unpackb(decompressed)
    return payload

def handle_message(message: mitmproxy.websocket.WebSocketMessage):
    msg = ''
    msge = ''
    clean = message.text  
    # clean = f"{message.content!r}"
    if any(x in clean for x in ['received_chat_message']):
        # print(clean[9:])
        prefix = clean[:9]
        r = json.loads(clean[9:])
        m = json.loads(r[1])

        payload = m['payload']
        payloader = m['payload']
        # payloader = payload.replace("\"", '')
        # payloader = payload.replace('\\', '')
        m['payload'] = payload
        r[1] = json.dumps(m)
        clean = prefix + json.dumps(r)

        themes = r[1]
        msg = simplejson.dumps(payloader, indent=4, sort_keys=True)
        msge = json.loads(payloader)
        x = json.loads(payloader)
        userId = x['userId']
        meseg = x['data']
        # print(x)
        return userId, meseg
    return '', ''
def handle_response(message: mitmproxy.websocket.WebSocketMessage):
    data = message.text
    s = json.loads(data)
    d = decompress(s['payload'])
    return QuestSystemScheduleInfo(d)

def websocket_message(flow: http.HTTPFlow):
    assert flow.websocket is not None  # make type checker happy
    # get the latest message
    message = flow.websocket.messages[-1]
    # was the message sent from the client or server?
    uid, mes = handle_message(message)
    #Kureha Saltellia - 822858185
    #Yangguo Astel - 275893242
    #Kokpit Astel - 337408637 
    #Asphy Astel - 909541004
    #crayons Astel - 662178705
    #Nanuwu Astel - 959805580
    uidList = [822858185, 275893242, 337408637, 909541004, 662178705, 959805580]
    unameList = ['kure', 'yg', 'kokpit', 'asphy', 'crayons', 'nanuwu']
    # print(uid)
    mes.replace("\n", '')
    if uid in uidList:
        if mes == 'Congrats!':
            # print('GAY')
            # puri.Purification().coloSP()
            if(uid == 822858185):
                # print('Kureha')
                df = open("TESTA.json", "a")
                df.write('shit')
                df.close()
                puri.Purification().getAP()
        
    # if(uid != ''):
    #     print(uid)

# import time, json, zlib, msgpack, base64
# from mitmproxy import ctx, http, websocket
# class WSS:

#     def decompress(self, string: str):
#         while '\/' in string:
#             string = string.replace('\/', '/')

#         decoded = base64.b64decode(string)
#         decompressed = zlib.decompress(decoded)
#         payload = msgpack.unpackb(decompressed)
#         return payload

#     def handle_message(self, message: websocket.WebSocketMessage):
#         msg = time.strftime('[%Y-%m-%d %H-%M-%S]')
#         if message.from_client:
#             kon = f"\n\n\nClient sent a message: {message.content!r}\n\n\n"
#         else:
#             kon = f"\n\n\nServer sent a message: {message.content!r}\n\n\n"
#         df = open("WAWA.json", "a")
#         df.write(kon)
#         df.close()
#         # clean = f"{message.content}"
#         # if any(x in clean for x in ['scheduler_uuid', 'user_act']):
#         #     prefix = clean[:9]
#         #     r = json.loads(clean[9:])
#         #     m = json.loads(r[1])
#         # m = json.loads(clean)
#         # payload = self.decompress(m['payload'].replace('"', ''))

#         # m['payload'] = payload
#         # r[1] = json.dumps(m)
#         # clean = prefix + json.dumps(r)

#         # msg += (' [OUT] >> ' if message.from_client else ' [IN]  << ') + clean
#         # df = open("WAWA.json", "a")
#         # df.write(clean)
#         # df.close()

#     def websocket_message(self, flow: http.HTTPFlow):
#         # get the latest message
#         message = flow.websocket.messages[-1]

#         # was the message sent from the client or server?
#         self.handle_message(message)

# addons = [
#     WSS()
# ]