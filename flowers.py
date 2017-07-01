import discord
from discord.ext import commands
import random
import json
import asyncio
import operator
from utils import checks


def flower_db_edit(user, json_data, count):
    user_id = str(user.id)
    json_data[user_id] = int(count)
    with open('flowers.json', 'w') as json_file:
        json_file.write(json.dumps(json_data, indent=2))



async def do_flower(message, bot, json_data, random_word = '', reward=1, flower_type='flower',
                    flower_url='https://i.imgur.com/1pIkDl2.jpg'):
    flower_embed = discord.Embed(description='A {} has appeared! '
                                             'Type "{}pick{}" to pick it!'.format(flower_type, bot.command_prefix, random_word))
    flower_embed.set_image(url=flower_url)
    flower_message = await bot.send_message(message.channel, embed=flower_embed)
    response = await bot.wait_for_message(timeout=30, content='{}pick{}'.format(bot.command_prefix, random_word))
    if response is None:
        wilt_message = await bot.send_message(message.channel, 'The {} wilted!'.format(flower_type))
        await asyncio.sleep(5)
        await bot.delete_message(flower_message)
        await bot.delete_message(wilt_message)
    else:
        flower_db_edit(response.author, json_data, json_data.get(response.author.id, 0) + reward)
        pick_message = await bot.send_message(message.channel,
                                              "{} has picked the {}! They now have {} {}s!"
                                              .format(response.author.display_name,
                                                      flower_type,
                                                      json_data.get(response.author.id, 0),
                                                      flower_type))

        await asyncio.sleep(10)

        def check(message):
            return '{}pick'.format(bot.command_prefix) in message.content

        await bot.purge_from(message.channel, after=flower_message, check=check)
        await bot.delete_message(flower_message)
        await bot.delete_message(pick_message)


def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile):
        if random.randrange(num + 2): continue
        line = aline
    return str(line)


class Flowers():
    def __init__(self, bot):
        with open('flowers.json') as json_file:
            json_data = json.load(json_file)
        self.bot = bot
        self.json_data = json_data
        self.words = []
        with open('words.txt') as file:
            for line in file:
                self.words.append(line.replace('\n',''))


    def flower_cost(flowers, *exclude_channels):
        def flower_cost_check(ctx):
            if ctx.message.channel.name in exclude_channels:
                return True
            if ctx.cog is None:
                return True
            try:
                if ctx.cog.json_data[ctx.message.author.id] >= flowers:
                    ctx.cog.json_data[ctx.message.author.id] = ctx.cog.json_data[ctx.message.author.id] - flowers
                    ctx.cog.json_data['263858105639501826'] = ctx.cog.json_data['263858105639501826'] + flowers
                    with open('flowers.json', 'w') as json_file:
                        json_file.write(json.dumps(ctx.cog.json_data, indent=2))
                    return True
            except KeyError:
                return False
            return False

        return commands.check(flower_cost_check)

    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        if message.channel.name == 'shitposting':
            if random.randint(0, 100) == 1:
                await do_flower(message, self.bot, self.json_data, random_word=' ' + random.choice(self.words), reward=1, flower_type='flower')
        elif random.randint(0, 500) == 1:
            await do_flower(message, self.bot, self.json_data, random_word=' ' + random.choice(self.words), reward=random.randint(5, 10), flower_type='flower')

    @commands.command(hidden=True)
    async def pick(self):
        pass

    @commands.group(pass_context=True, aliases=['flower'], invoke_without_command=True)
    async def flowers(self, ctx):
        """Gets the flower leaderboards, if users are mentioned in the command, gets their stats specifically"""
        with open('flowers.json') as json_file:
            json_data = json.load(json_file)
        if not ctx.message.mentions:
            flower_board_message = ['Flower leaderboards!\n```']

            sorted_json = sorted(json_data.items(), key=operator.itemgetter(1), reverse=True)

            for data in sorted_json[:10]:
                msg_to_append = '{} : {}'.format(discord.utils.get(ctx.message.server.members, id=data[0]), data[1])
                flower_board_message.append(msg_to_append)

            flower_board_message.append('```')

            flower_board_message = '\n'.join(flower_board_message)
            await self.bot.say(flower_board_message)

        else:
            message_list = []
            for member in ctx.message.mentions[:10]:
                try:
                    message_list.append('{} has {} flowers!'.format(member.display_name, json_data[member.id]))
                except KeyError:
                    message_list.append('{} has no flowers!'.format(member.display_name))
            await self.bot.say('\n'.join(message_list))

    # @flowers.command(pass_context=True)
    # async def list(self, ctx):


    @flowers.command()
    @checks.mod_or_permissions(manage_roles=True)
    @checks.is_owner()
    async def edit(self, user: discord.Member, count):
        """Admin command to set the flowers of a specific user"""
        json_data = self.json_data
        user_id = str(user.id)
        try:
            await self.bot.say(
                '{} had {} flowers, now they have {}'.format(user.display_name, json_data.get(user.id, 0), count))
            json_data[user_id] = int(count)
        except KeyError:
            return
        except ValueError:
            await self.bot.say('{} is not an integer!'.format(count))
        flower_db_edit(user, json_data, count)

    @flowers.command(pass_context=True)
    @checks.is_owner()
    async def make(self, ctx):
        """Causes a flower spawn"""
        await do_flower(ctx.message, self.bot, self.json_data, random_word=' ' + random.choice(self.words),
                        reward=random.randint(5, 10), flower_type='flower')

    @flowers.command(pass_context=True)
    @flower_cost(5)
    async def nick(self, ctx, user: discord.Member, *, nickname):
        """Changes someone's name at the cost of 5 flowers"""
        if user == ctx.message.server.me:
            return
        try:
            await self.bot.change_nickname(user, nickname)
            await self.bot.add_reaction(ctx.message, '✅')
        except Exception as e:
            await self.bot.say(e)

    @nick.error
    async def flowernick_error(self, error, ctx):
        if isinstance(error, discord.ext.commands.errors.BadArgument):
            await self.bot.send_message(ctx.message.channel, error)
        else:
            await self.bot.say(error)

    @flowers.command(pass_context=True)
    async def give(self, ctx, count, *, user: discord.Member):
        """Gives X flowers to Y!"""
        json_data = self.json_data
        count = abs(int(count))
        if json_data[ctx.message.author.id] < int(count):
            await self.bot.say('You are too poor')
        else:
            await self.bot.say('{} gave {} {} flowers!'.format(
                ctx.message.author.display_name, user.display_name, count))
            json_data[ctx.message.author.id] = json_data[ctx.message.author.id] - count
            json_data[user.id] = json_data.get(user.id, 0) + count
            with open('flowers.json', 'w') as json_file:
                json_file.write(json.dumps(json_data, indent=2))

    @flowers.command(pass_context=True)
    @flower_cost(5)
    async def plant(self, ctx):
        """Plant 5 flowers and one will pop up soon!"""
        time_to_sleep = random.randint(60, 1000)
        await self.bot.say('{} planted a flower! It will sprout in about {} seconds!'
                           .format(ctx.message.author.display_name, str(time_to_sleep + random.randint(-30, 30))))
        await asyncio.sleep(time_to_sleep)
        await do_flower(ctx.message, self.bot, self.json_data, random_word=random.choice[self.words], reward=random.randint(5,10))

    @commands.command(pass_context=True)
    @flower_cost(5, 'shitposting')
    async def angry(self, ctx, *, string='missing\n                      arguments'):
        from PIL import Image, ImageDraw, ImageFont
        import aiohttp
        import io
        import re

        def make_angry(angry, avatar, text):
            avatar = avatar.resize((62, 62), resample=3)
            angry.paste(avatar, box=(14, 14))
            fnt = ImageFont.truetype('assets/LeviWindows.ttf', 22)
            d = ImageDraw.Draw(angry)
            d.fontmode = "1"
            d.multiline_text((109, -1), "I am angry\n ANGRY ABOUT {}".format(text.upper()),
                             fill=(0, 0, 0), font=fnt, spacing=-5)
            imagefileobject = io.BytesIO()
            angry.save(imagefileobject, format='png')
            imagefileobject.seek(0)
            return imagefileobject

        with Image.open('assets/angry.png').convert('RGBA') as angry:
            if not ctx.message.mentions:
                avatar_url = ctx.message.author.avatar_url
            else:
                avatar_url = ctx.message.mentions[0].avatar_url
                string = re.sub(r"<@!?[0-9]*> ?", '', string)
            with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    with Image.open(io.BytesIO(await resp.read())).convert('RGBA') as avatar:
                        angry_image = await self.bot.loop.run_in_executor(None, make_angry, angry, avatar, string)
                        await self.bot.send_file(ctx.message.channel, fp=angry_image, filename='angry.png')

    @angry.error
    async def angry_error(self, error, ctx):
        await self.bot.say('You are too poor!')


def setup(bot):
    bot.add_cog(Flowers(bot))
