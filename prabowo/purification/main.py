# bot.py
import os
from urllib.request import urlopen
import discord
from discord.ext import commands
import json
import requests
import asyncio
from SINoAPI import API
import aiomysql
import simplejson
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_VER = '27.1.0'
SECRET = b'E0pBnbdmU9+rLfQ4'
loop = asyncio.get_event_loop()
async def get_sinover():
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("SELECT * from app_version")
    r = await cur.fetchone()
    await cur.close()
    conn.close()

    return r[0]

async def get_user(discid: int):
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("SELECT * from user where id = %s", [discid])
    r = await cur.fetchone()
    await cur.close()
    conn.close()

    return r

async def get_user_active():
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("SELECT * from user where active")
    r = await cur.fetchall()
    await cur.close()
    conn.close()

    return r

async def get_all_user():
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("SELECT * from user")
    r = await cur.fetchall()
    await cur.close()
    conn.close()

    return r

async def toggle_all_off():
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("UPDATE user set active = 0 where 1")
    await conn.commit()
    await cur.close()
    conn.close()

    return 'a'

async def toggleActive(discid: int, active: int):
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    changed = 0 if active == 1 else 1 

    cur = await conn.cursor()
    await cur.execute("UPDATE user set active = %s where id = %s", [changed, discid])
    await conn.commit()
    await cur.close()
    conn.close()

    return changed

async def change_sp(discid: int, sp: int):
    conn = await aiomysql.connect(host=os.getenv('host'), port=3306,
                                       user=os.getenv('user'), password='', db=os.getenv('database'),
                                       loop=loop)

    cur = await conn.cursor()
    await cur.execute("UPDATE user set recover = %s where id = %s", [sp, discid])
    await conn.commit()
    await cur.close()
    conn.close()

    return sp

client = commands.Bot(command_prefix='*', description="Kurebot v.0.69")

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def checkver(ctx):
    await ctx.send(await get_sinover())

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def testconnect(ctx):
    ACC = await get_all_user()
    embed = discord.Embed(title="All Connected Accounts", description="-", color=0xff00ff)
    for x in ACC:
        print(x[1])
        try:
            dat = Spgod(x[4], x[2], x[5], x[3]).getStatus()
            embed.add_field(name=x[1], value="Account Connected to : " + dat['payload']['userData']['name'], inline=False)
        except:
            embed.add_field(name=x[1], value="Account Failed to Connect", inline=False)
    await ctx.send(embed=embed)

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def togglealloff(ctx):
    try:
        ACC = await toggle_all_off()
        embed = discord.Embed(title="All Account Toggled to Inactive Success", description="-", color=0x00ff00)
    except:
        embed = discord.Embed(title="All Account Toggled to Inactive Failed", description="-", color=0xff0000)
    
    await ctx.send(embed=embed)

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def status(ctx, user: discord.User=None):
    if not user:
        userId = ctx.author.id
    else:
        userId = user.id
    ACC = await get_user(userId)
    if ACC == None:
        embed = discord.Embed(title="Status", description="Account not Found", color=0xff0000)
    else:
        try:
            dat = Spgod(ACC[4], ACC[2], ACC[5], ACC[3]).getStatus()
            embed = discord.Embed(title="Status", description="Account Connected to : " + dat['payload']['userData']['name'], color=0x00ff00)
            embed.add_field(name="SP per Recover", value=str(ACC[7]) + " per " + str(ACC[6]) + " seconds", inline=False)
            embed.add_field(name="Auto SP Status", value="Active for Colo" if ACC[8] == 1 else "Inactive for Colo", inline=False)
            embed.add_field(name="TS", value=str(ACC[9]), inline=False)
        except:
            embed = discord.Embed(title="Status", description="Account Failed to Connect | Contact Kureha", color=0xff0000)

    await ctx.send(embed=embed)

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def toggle(ctx, user: discord.User=None):
    if not user:
        userId = ctx.author.id
    else:
        userId = user.id
    ACC = await get_user(userId)
    if ACC == None:
        embed = discord.Embed(title="Status", description="Account not Found", color=0xff0000)
    else:
        try:
            res = await toggleActive(userId, ACC[8])
            embed = discord.Embed(title="Status", description="AutoSP is Toggled : " + 'Active' if res == 1 else "AutoSP is Toggled : " + 'Inactive', color=0x00ff00 if res == 1 else 0xff00ff)

        except:
            embed = discord.Embed(title="Status", description="Toggle Failed | Contact Kureha", color=0xff0000)

    await ctx.send(embed=embed)

@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def changesp(ctx, val: int=None, user: discord.User=None):
    if not user:
        userId = ctx.author.id
    else:
        userId = user.id    
    ACC = await get_user(userId)
    if ACC == None:
        embed = discord.Embed(title="Status", description="Account not Found", color=0xff0000)
    else:
        if val is None:
            embed = discord.Embed(title="Status", description="Command Usage *changesp <number> | Maximum 200", color=0xff0000)
        elif val > 200:
            embed = discord.Embed(title="Status", description="SP cant over 200", color=0xff0000)
        else:
            try:
                res = await change_sp(userId, val)
                embed = discord.Embed(title="Status", description="SP Changed to " + str(res), color=0x00ff00)
            except:
                embed = discord.Embed(title="Status", description="SP Change Failed | Contact Kureha", color=0xff0000)
    await ctx.send(embed=embed)
@client.command()
@commands.has_any_role('Kure-o-PP Cult', 'Nure-o-PP Cult')
async def getactive(ctx):
    ACC = await get_user_active()
    embed = discord.Embed(title="Status", description="Auto SP Active User", color=0xff00ff)
    for x in ACC:
        embed.add_field(name=x[1], value=str(x[7]) + " per " + str(x[6]) + " seconds", inline=False)
    await ctx.send(embed=embed)
@client.command()
@commands.has_role('Kure-o-PP Cult')
async def forcesp(ctx, user: discord.User=None):
    if not user:
        userId = ctx.author.id
    else:
        userId = user.id
    ACC = await get_user(userId)
    if ACC == None:
        embed = discord.Embed(title="Status", description="Account not Found", color=0xff0000)
    else:
        now = datetime.datetime.now()
        if now.hour == 21 and 0 <= now.minute <= 20:
            try:
                res = Spgod(ACC[4], ACC[2], ACC[5], ACC[3]).forceSP(100)
                embed = discord.Embed(title="Status", description="Forcing SP add by : 100", color=0x00ff00)
            except:
                embed = discord.Embed(title="Status", description="Forcing SP Failed | Contact Kureha", color=0xff0000)
        else:
            embed = discord.Embed(title="Status", description="It is not Colo time yet", color=0xff0000)
    await ctx.send(embed=embed)

@client.command()
@commands.has_role('Nure-o-PP Cult')
async def forcespsalt(ctx, user: discord.User=None):
    if not user:
        userId = ctx.author.id
    else:
        userId = user.id
    ACC = await get_user(userId)
    if ACC == None:
        embed = discord.Embed(title="Status", description="Account not Found", color=0xff0000)
    else:
        now = datetime.datetime.now()
        if now.hour == 20 and 0 <= now.minute <= 20:
            try:
                res = Spgod(ACC[4], ACC[2], ACC[5], ACC[3]).forceSP(100)
                embed = discord.Embed(title="Status", description="Forcing SP add by : 100", color=0x00ff00)
            except:
                embed = discord.Embed(title="Status", description="Forcing SP Failed | Contact Kureha", color=0xff0000)
        else:
            embed = discord.Embed(title="Status", description="It is not Colo time yet", color=0xff0000)
    await ctx.send(embed=embed)

class Spgod():
    def __init__(self, userid, uuid, priv, sess):
        self.api = API(userid, APP_VER, uuid, priv, sess) # kure

    def getStatus(self):

        res = self.api.POST__api_user_get_user_data()
        a = simplejson.dumps(res, indent=4, sort_keys=True)
        b = json.loads(a)
        return b

    def forceSP(self, val:int):
        res = self.api.POST__api_gvg_sp(val)
        return res
        

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Your mom"))
    print(f'{client.user} has connected to Discord!')
client.run(TOKEN)
