import os
from urllib.request import urlopen
import discord
import json
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ACC1 = os.getenv('ACCOUNTSATU')
ACC2 = os.getenv('ACCOUNTDUA')

url = "http://xvc.cleverapps.io/getuser2/" + ACC2
response = requests.get(url).text

data_json = json.loads(response)
  
# print the json response
print(data_json['payload']['userData']['stamina'])