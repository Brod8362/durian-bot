#!/bin/python3
from ntpath import join
import discord
import sqlite3 
import toml
import os
import time

# this is a hastily thrown together bot that doesn't really use a lot of good pratices

join_time = {}
conf = {}
conn = sqlite3.connect("durian.db")
dclient = discord.Client()

def db_setup():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS time (user INTEGER NOT NULL PRIMARY KEY, time INTEGER)")
    conn.commit()
    cur.close()

def db_update_time(user, time_to_add):
    cur = conn.cursor()
    cur.execute("INSERT INTO time VALUES (?, ?) ON CONFLICT(user) DO UPDATE SET time = time + ?", (user, time_to_add, time_to_add))
    conn.commit()
    cur.close()

def db_get_all_time():
    cur = conn.cursor()
    kv = {}
    cur.execute("SELECT user, time FROM time")
    rs = cur.fetchall()
    for row in rs:
        kv[row[0]] = row[1]
    cur.close()
    return kv

@dclient.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if (before.channel == None or before.channel.id != conf["channel"]) and after.channel.id == conf["channel"]:
        join_time[member.id] = time.time()
    elif before.channel.id == conf["channel"] and (after.channel == None or after.channel.id != conf["channel"]):
        if member.id not in join_time: # can happen if the bot starts up and people are already in the channel
            return
        elapsed = time.time() - join_time.pop(member.id)
        db_update_time(member.id, elapsed)

def nice_time(seconds) -> str:
    units = {
        "d": 60*60*24,
        "h": 60*60,
        "m": 60,
        "s": 1
    }
    remaining = int(seconds)
    output = []
    for unit in units:
        ratio = remaining/units[unit]
        if ratio >= 1.0:
            remaining -= int(ratio)*units[unit]
            output.append(f"{int(ratio)}{unit}")
    return " ".join(output)

@dclient.event
async def on_message(message):
    if message.content.startswith("$lb"):
        times = db_get_all_time()
        for user in join_time:
            if user not in times:
                times[user] = 0
            times[user] += time.time() - join_time[user]
        lb = list(times.items())
        lb.sort(key= lambda x: x[1], reverse=True)
        entries = ["```", "== DURIAN LEADERBOARD =="]
        for t in lb[:10]:
            user = await dclient.fetch_user(t[0])
            entries.append(f"{user.name}: {nice_time(t[1])}")
        entries.append("```")
        await message.channel.send("\n".join(entries))

@dclient.event
async def on_ready():
    print("ok")
    activity = discord.Game("$lb", type=3)
    await dclient.change_presence(status=discord.Status.online, activity=activity)
    chan = await dclient.fetch_channel(conf["channel"])
    for x in chan.members:
        print(x)
        join_time[x.id] = time.time()

def main():
    if not os.path.exists("config.toml"):
        print("could not find config.toml")
        exit(1)
    global conf
    with open("config.toml", "r") as fd:
        conf = toml.loads(fd.read())
    required = ["token", "channel"]
    for x in required:
        if x not in conf:
            print(f"required value {x} missing")
            exit(1)
    db_setup()
    dclient.run(conf["token"])

if __name__ == "__main__":
    main()