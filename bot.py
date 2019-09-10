import os
import json
import re

import numpy as np
import pandas as pd

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

res = None
channel = None

emojis = {
    '1⃣': 1,
    '2⃣': 2,
    '3⃣': 3,
    '4⃣': 4,
    '5⃣': 5,
    '6⃣': 6,
    '7⃣': 7,
    '8⃣': 8,
    '9⃣': 9,
    '🔟': 10,
}

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    for guild in bot.guilds:
        for chan in guild.channels:
            if chan.name == 'pouetmusic':
                global channel
                channel = chan
                break

    with open('results.json', 'r') as f:
        global res
        res = json.load(f)

@bot.command(name='submit', help='Submit a song to votes', pass_context=True)
async def submit_song(ctx, url: str):
    response = '{} submitted {}'.format(ctx.message.author, url)
    await ctx.message.delete()

    if re.match(regex, url) is None:
        return
    
    tmp = await ctx.send(response)

    res.update({str(tmp.id): {
        'url': url,
        'submittedBy': str(ctx.message.author),
        'marks': {}
    }})
    with open('results.json', "w") as write_file:
        json.dump(res, write_file)

@bot.command(name='result', help='Get results', pass_context=True)
async def result(ctx, top: int=5):
    clm = ['Url', 'User', 'Votes', 'Score']
    df = pd.DataFrame(columns=clm)

    for key in res.keys():
        tmp = []
        for notes in res[key]['marks']:
            tmp.append(res[key]['marks'][notes])
        
        if tmp != []:
            tmp = np.array(tmp)
            df = df.append(pd.Series([res[key]['url'].split('//')[1], res[key]['submittedBy'], len(tmp), tmp.mean()], index=clm), ignore_index=True)

    response = df.set_index('Url').sort_values('Score', ascending=False).head(top)
    response = '```{}```'.format(response)
    await ctx.send(response)

@bot.command(name='stats', help='Get stats', pass_context=True)
async def stats(ctx, top: int=5):
    df = pd.DataFrame()

    for key in res.keys():
        tmp = pd.Series(res[key]['marks'])
        tmp['submittedBy'] = res[key]['submittedBy']
        df = df.append(tmp, ignore_index=True)

    nb_videos = df['submittedBy'].value_counts().sort_values(ascending=False).head(top)
    marks_given = df.mean().sort_values(ascending=False).head(top)
    marks_received = (df.groupby('submittedBy').sum().sum(axis=1) / df.groupby('submittedBy').count().sum(axis=1)).sort_values(ascending=False).head(top)

    response = '```Nombre de vidéos postées:\n{}\n\nMoyenne des notes données:\n{}\n\nMoyenne des notes reçues:\n{}```'.format(nb_videos, marks_given, marks_received)
    await ctx.send(response)

@bot.event
async def on_raw_reaction_add(payload):
    message_id = payload.message_id
    msg = await channel.history().find(lambda m: m.id == message_id)
    user = bot.get_user(payload.user_id)
    emoji = payload.emoji

    if user.name in res[str(message_id)]['marks'] or str(emoji) not in emojis:
        await msg.remove_reaction(emoji, user)
    else:
        res[str(message_id)]['marks'].update({user.name: emojis[str(emoji)]})

    with open('results.json', "w") as write_file:
        json.dump(res, write_file)


@bot.event
async def on_raw_reaction_remove(payload):
    message_id = payload.message_id
    msg = await channel.history().find(lambda m: m.id == message_id)
    user = bot.get_user(payload.user_id)
    emoji = payload.emoji

    if user.name in res[str(message_id)]['marks'] and res[str(message_id)]['marks'][user.name] == emojis[str(emoji)]:
        res[str(message_id)]['marks'].pop(user.name, None)

    with open('results.json', "w") as write_file:
        json.dump(res, write_file)

bot.run(token)