import aiohttp
import discord
from discord.ext import commands
from utils import checks
import random
import markovify
import asyncio


def markovstring(filename='log.txt'):
    with open(filename, 'r', encoding='utf8') as file:
        text = file.read()
        text_model = markovify.NewlineText(text)
        while True:
            message = text_model.make_sentence()
            if message is not None:
                return message
                break


def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile):
        if random.randrange(num + 2):
            continue
        line = aline
    return str(line)


class ShitPosting():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def sw(self, cxt):
        """Makes autoSW say something! Only works in #shitpost, Skeleton Bones is stupid"""
        if cxt.message.channel.id == '298667118810103808' or cxt.message.channel.id == '299029980858417153':
            await self.bot.say(markovstring())
        else:
            if cxt.message.author.id == '129855424198475776':
                await self.bot.say('Vex is an amazing human being')
            else:
                file = open('insults.txt', 'r')
                await self.bot.say(str(random_line(file)))

    @commands.command()
    @checks.is_botbanned()
    async def makeinsult(self):
        await self.bot.say(markovstring('insults.txt'))

    @commands.command()
    @checks.is_botbanned()
    async def swinsult(self, weight1=1, weight2=2):
        """Makes SW insult you! Poorly! Usage: &swinsult <weight of SW> <weight of insults>"""
        text1 = open('log.txt', encoding='utf8').read()
        text2 = open('insults.txt').read()
        model1 = markovify.Text(text1)
        model2 = markovify.Text(text2)
        comb_model = markovify.combine([model1, model2], [weight1, weight2])
        while True:
            msg = comb_model.make_sentence()
            if msg is not None:
                await self.bot.say(msg)
                break

    @commands.command()
    @checks.is_botbanned()
    async def bane(self):
        text = open('banemarkov.txt').read()
        model1 = markovify.Text(text)
        while True:
            strn = model1.make_sentence()
            if strn is not None:
                await self.bot.say(strn)
                break

    @commands.command()
    @checks.is_botbanned()
    async def baneinsult(self, weight1=1, weight2=2):
        """Who fucking knows. Usage: &swinsult <weight of insults> <weight of bane>"""
        text1 = open('insults.txt', encoding='utf8').read()
        text2 = open('banemarkov.txt').read()
        model1 = markovify.Text(text1)
        model2 = markovify.Text(text2)
        comb_model = markovify.combine([model1, model2], [weight1, weight2])
        while True:
            msg = comb_model.make_sentence()
            if msg is not None:
                await self.bot.say(msg)
                break

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def isshitter(self, ctx, *, usr=None):
        """Uses only the most advanced algorithms avaliable to man to carefully decide if someone is shit!"""
        isshit = random.choice(['', 'not '])
        mentions = ctx.message.mentions
        if len(mentions) != 0:
            memb = mentions[0]
            if memb.id == '129855424198475776':
                await self.bot.say('Vex is not a shitter')
            elif memb == ctx.message.author:
                await self.bot.say('You know what you are.')
            else:
                if isshit == '':
                    try:
                        await self.bot.change_nickname(memb, memb.display_name + '🔰')
                    except discord.Forbidden:
                        pass
                await self.bot.say('{} is {}a shitter'.format(memb.display_name, isshit))
        elif len(mentions) == 0:
            if usr == 'Vex':
                await self.bot.say('Vex is not a shitter')
            elif usr in ctx.message.author.name or usr in ctx.message.author.display_name:
                await self.bot.say('You know what you are.')
            else:
                for memb in ctx.message.server.members:
                    if usr.lower() in memb.display_name.lower() or usr.lower() in memb.name.lower():
                        if isshit == '':
                            try:
                                await self.bot.change_nickname(memb, memb.display_name + '🔰')
                            except discord.Forbidden:
                                pass
                        await self.bot.say('{} is {}a shitter'.format(memb.display_name, isshit))
                        break
                else:
                    await self.bot.say('{} is {}a shitter'.format(usr, isshit))

    @commands.command(pass_context=True)
    @commands.cooldown(1, 60, type=commands.BucketType.server)
    async def cat(self, ctx):
        """Usage: Use it, and it gets a cat."""
        with aiohttp.ClientSession() as session:
            async with session.get('http://random.cat/meow') as r:
                if r.status == 200:
                    js = await r.json()
                    await self.bot.send_message(ctx.message.channel, js['file'])

    @commands.command()
    @checks.is_owner()
    async def makeposts(number):
        """Vex only! Creates a file of things autosw would say."""
        with open("sayings.txt", 'a', encoding='utf8') as file, open("log.txt", 'r', encoding='utf8') as markov:
            text = markov.read()
            text_model = markovify.NewlineText(text)
            for i in range(int(number)):
                while True:
                    message = text_model.make_sentence()
                    if message is not None:
                        file.write(message + '\n')
                        break
            file.close()

    @commands.command(pass_context=True)
    async def roulette(self, ctx, bullets:int=1):
        """A simple, stupid game of russian roulette. Load 1-6 bullets in the chamber,
the less bullets you load, the longer the penalty."""
        bannedrole = discord.utils.get(ctx.message.server.roles, name='banned')
        async def tempban(member, seconds):
            await self.bot.add_roles(member, bannedrole)
            await asyncio.sleep(seconds)
            await self.bot.remove_roles(member, bannedrole)
        if bannedrole in ctx.message.author.roles:
            await self.bot.say('{} is already dead and as such, lacks the nessicary things to either load or fire a '
                               'gun!'.format(ctx.message.author.display_name))
        elif bullets < 0:
            await self.bot.say('{} removes the nothing from the revolver and causes a black hole!'.format(
                ctx.message.author.display_name))
            await tempban(ctx.message.author, 30)
        elif bullets == 0:
            await self.bot.say('{} loads nothing into the revolver and nothing happens!'.format(
                ctx.message.author.display_name))
        elif bullets >= 6:
            await self.bot.say('{} loads the revolver full of bullets and shoots themselves in the head!'
                               .format(ctx.message.author.display_name))
            await tempban(ctx.message.author, 30)
        elif bullets < 6:
            message = await self.bot.say('{} loads {} bullet{} in the chamber and pulls the trigger...'
                                         .format(ctx.message.author.display_name, str(bullets),
                                                 '' if bullets == 1 else 's'))
            await asyncio.sleep(5)
            if random.randint(1,6) <= bullets:
                await self.bot.edit_message(message, message.content+'\n and shoots themselves in the head!')
                await tempban(ctx.message.author, (6-bullets)*30)
            else:
                await self.bot.edit_message(message, message.content + '\n click!')





def setup(bot):
    bot.add_cog(ShitPosting(bot))
