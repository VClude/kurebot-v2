import json, base64, zlib, msgpack
from .struct.quest_struct import QuestSystemScheduleInfo

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