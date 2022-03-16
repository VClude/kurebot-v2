import mitmproxy.websocket, time, json, zlib, msgpack, base64
from quests_deserializer import QuestSystemScheduleInfo
from mitmproxy import ctx, http
import re

# def decompress(string: bytes):
#     while '\/' in string:
#         string = string.replace('\/', '/')

#     # decoded = base64.b64decode(string)
#     # decompressed = zlib.decompress(decoded)
#     # payload = msgpack.unpackb(decompressed)
#     return string


def websocket_message(flow: http.HTTPFlow):
    assert flow.websocket is not None  # make type checker happy
    # get the latest message
    message = flow.websocket.messages[-1]
    if message.from_client:
        kon = f"\n\n\nClient sent a message: \n {message.content!r}\n\n\n"
    else:
        kon = f"\n\n\nServer sent a message: \n {message.content!r}\n\n\n"
    # was the message sent from the client or server?
    df = open("WAWA2.json", "a")
    df.write(kon)
    df.close()

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