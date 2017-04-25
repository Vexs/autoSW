#!/usr/bin/env python3


import asyncio
import random
import discord
import markovify
from discord.ext import commands
from tokenfile import TOKEN
from utils import checks, chanUtils

bot = commands.Bot(command_prefix='&')

tfgthread = chanUtils.getthread('vg', '/tfg/')

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')


@bot.event
async def on_ready():
    print('Bot ready!')
    print('Logged in as ' + bot.user.name)
    print('-------')


@bot.event
async def on_message(message):
    await maksw(message)
    await recordsw(message)
    await bot.process_commands(message)

async def maksw(message):
    if message.channel.id == '298667118810103808':
        if 'sniperwaifu' in message.content or '156370484835909632' in message.content or str(
                message.server.me.id) in message.content:
            if message.author.id != '263858105639501826':
                if 'botBanned' not in [x.name for x in message.author.roles]:
                    await bot.send_message(message.channel, markovstring())


async def recordsw(message):
    if message.author.id == '156370484835909632':
        if message.content.lower() != 'sniperwaifu':
            with open('log.txt', 'a', encoding='utf8') as file:
                file.write(message.content + '\n')


def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile):
        if random.randrange(num + 2):
            continue
        line = aline
    return str(line)


@bot.command()
@checks.is_owner()
async def load(extension_name: str):
    """Loads an extension."""
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} loaded.".format(extension_name))


@bot.command()
@checks.is_owner()
async def unload(extension_name: str):
    """Unloads an extension."""
    bot.unload_extension(extension_name)
    await bot.say("{} unloaded.".format(extension_name))


@bot.command()
@checks.is_owner()
async def reload(extension_name: str):
    bot.unload_extension(extension_name)
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} reloaded.".format(extension_name))


async def getthreadupdates():
    global tfgthread
    await bot.wait_until_ready()
    mirrorchannel = discord.Object(id='275869654919151617')
    generalchannel = discord.Object(id='298667118810103808')
    while not bot.is_closed:
        newposts = tfgthread.update()
        if newposts == 0:
            oldurl = tfgthread.url
            oldtime = tfgthread.topic.datetime
            tfgthread = chanUtils.getthread()
            if oldurl != tfgthread.url and oldtime < tfgthread.topic.datetime:
                await bot.send_message(generalchannel, "New thread at: " + tfgthread.url)
        for post in tfgthread.posts[len(tfgthread.posts) - newposts:]:
            await bot.send_message(mirrorchannel, embed=chanUtils.posttoembed(post))
        await asyncio.sleep(60)  # task runs every 1 minutes


def markovstring(filename='log.txt'):
    with open(filename, 'r', encoding='utf8') as file:
        text = file.read()
        text_model = markovify.NewlineText(text)
        while True:
            message = text_model.make_sentence()
            if message is not None:
                return message
                break


startup_extensions = ["AdminTools", "ShitPosting", "ChanTools",
                      "RddtChecks", "ServerTools", "Music", "logs"]

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

bot.loop.create_task(getthreadupdates())
bot.run(TOKEN, bot=True)
