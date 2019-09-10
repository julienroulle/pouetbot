import os
import json
import re

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

    res.update({tmp.id: {
        'url': url,
        'submittedBy': str(ctx.message.author),
        'marks': {}
    }})
    with open('results.json', "w") as write_file:
        json.dump(res, write_file)

@bot.event
async def on_reaction_add(reaction, user):
    message_id = reaction.message.id

    if user.name in res[message_id]['marks'] or reaction.emoji not in emojis:
        await reaction.message.remove_reaction(reaction.emoji, user)
    else:
        res[message_id]['marks'].update({user.name: emojis[reaction.emoji]})

    with open('results.json', "w") as write_file:
        json.dump(res, write_file)

@bot.event
async def on_reaction_remove(reaction, user):
    message_id = reaction.message.id

    if user.name in res[message_id]['marks'] and res[message_id]['marks'][user.name] == emojis[reaction.emoji]:
        res[message_id]['marks'].pop(user.name, None)

    with open('results.json', "w") as write_file:
        json.dump(res, write_file)

bot.run(token)