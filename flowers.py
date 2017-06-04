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


async def do_flower(message, bot, json_data, reward=1, flower_type='flower'):
    flower_embed = discord.Embed(description='A {} has appeared! '
                                             'Type {}pick to pick it!'.format(flower_type, bot.command_prefix))
    flower_embed.set_image(url='https://i.imgur.com/1pIkDl2.jpg')
    flower_message = await bot.send_message(message.channel, embed=flower_embed)
    response = await bot.wait_for_message(timeout=30, content='{}pick'.format(bot.command_prefix))
    if response is None:
        wilt_message = await bot.send_message(message.channel, 'The flower wilted!')
        await asyncio.sleep(5)
        await bot.delete_message(flower_message)
        await bot.delete_message(wilt_message)
    else:
        flower_db_edit(response.author, json_data, json_data.get(response.author.id, 0) + reward)
        pick_message = await bot.send_message(message.channel,
                                              "{} has picked the {}! They now have {} flowers!"
                                              .format(response.author.display_name,
                                                      flower_type,
                                                      json_data.get(response.author.id, 0)))
        await asyncio.sleep(10)

        def check(message):
            return '{}pick'.format(bot.command_prefix) in message.content

        await bot.purge_from(message.channel, after=flower_message, check=check)
        await bot.delete_message(flower_message)
        await bot.delete_message(pick_message)


class Flowers():
    def __init__(self, bot):
        with open('flowers.json') as json_file:
            json_data = json.load(json_file)
        self.bot = bot
        self.json_data = json_data

    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        if message.channel.name == 'shitposting':
            if random.randint(0, 100) == 1:
                await do_flower(message, self.bot, self.json_data, 1, 'flower')
        elif random.randint(0, 500) == 1:
            await do_flower(message, self.bot, self.json_data, random.randint(1,10), 'flower')

    @commands.group(pass_context=True, aliases=['flower'])
    async def flowers(self, ctx):
        pass

    @flowers.command(pass_context=True)
    async def list(self, ctx):
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

    @flowers.command()
    @checks.mod_or_permissions(manage_roles=True)
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
        flower_db_edit(user,json_data,count)

    @flowers.command(pass_context=True)
    @checks.is_owner()
    async def make(self,ctx):
        """Causes a flower spawn"""
        await do_flower(ctx.message, self.bot, self.json_data)

    @flowers.command(pass_context=True)
    async def nick(self, ctx, user:discord.Member, *, nickname):
        """Changes someone's name at the cost of 5 flowers"""
        if user == ctx.message.server.me:
            return
        json_data = self.json_data
        if json_data[ctx.message.author.id] >= 5:
            flower_db_edit(ctx.message.author, json_data, json_data[ctx.message.author.id]-5)
            try:
                await self.bot.change_nickname(user, nickname)
                await self.bot.add_reaction(ctx.message, '✅')
            except Exception as e:
                await self.bot.say(e)
        else:
            await self.bot.say('You need 5 flowers to change a nickname! You have {}'.format(json_data[user.id]))

    @nick.error
    async def flowernick_error(self, error, ctx):
        if isinstance(error, discord.ext.commands.errors.BadArgument):
            await self.bot.send_message(ctx.message.channel, error)

    @flowers.command(pass_context=True)
    async def give(self, ctx, count, *, user: discord.Member):
        """Gives X flowers to Y!"""
        json_data = self.json_data
        if json_data[ctx.message.author.id] < int(count):
            await self.bot.say('You are too poor')
        else:
            await self.bot.say('{} gave {} {} flowers!'.format(
                ctx.message.author.display_name, user.display_name, count))
            json_data[ctx.message.author.id] - count
            json_data[user.id] + count
            with open('flowers.json', 'w') as json_file:
                json_file.write(json.dumps(json_data, indent=2))


def setup(bot):
    bot.add_cog(Flowers(bot))
