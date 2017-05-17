import discord
from discord.ext import commands
import random
import json
import asyncio
import operator
from utils import checks

# todo race condition with way of getting/saving flowers maybe?
def flower_db_get(user):
    with open('flowers.json') as json_file:
        json_data = json.load(json_file)
        user_id = str(user.id)
        try:
            # return json_data[user_id]['FlowerCount']
            return json_data[user_id]
        except KeyError:
            return 0


def flower_db_edit(user, count):
    with open('flowers.json') as json_file:
        json_data = json.load(json_file)
        user_id = str(user.id)

        try:
            json_data[user_id] = json_data[user_id] + count
        except KeyError:
            json_data[user_id] = 1

            # try:
            #    json_data[user_id]['FlowerCount'] = json_data[user_id]['FlowerCount'] + count
            # except KeyError:
            #    json_data[user_id] = {'FlowerCount': 1}

    with open('flowers.json', 'w') as json_file:
        json_file.write(json.dumps(json_data, indent=2))


async def do_flower(message, bot, reward=1, flower_type='flower'):
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
        flower_db_edit(response.author, reward)
        pick_message = await bot.send_message(message.channel,
                                              "{} has picked the {}! They now have {} flowers!"
                                              .format(response.author.display_name,
                                                      flower_type,
                                                      flower_db_get(response.author)))
        await asyncio.sleep(10)

        def check(message):
            return '{}pick'.format(bot.command_prefix) in message.content

        await bot.purge_from(message.channel, after=flower_message, check=check)
        await bot.delete_message(flower_message)
        await bot.delete_message(pick_message)


class Flowers():
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        if message.author == message.server.me:
            return
        if self.bot.command_prefix + 'pick' in message.content:
            return
        if message.channel.name == 'shitposting':
            if random.randint(0, 100) == 1:
                await do_flower(message, self.bot)
        elif random.randint(0, 2000) == 1:
            await do_flower(message, self.bot, 10)

    @commands.command(pass_context=True, name='flowers')
    async def _flowers(self, ctx):
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

    @commands.command()
    @checks.mod_or_permissions(manage_roles=True)
    async def editflowers(self, user: discord.Member, count):
        """Admin command to set the flowers of a specific user"""
        with open('flowers.json') as json_file:
            json_data = json.load(json_file)
            user_id = str(user.id)

            try:
                await self.bot.say(
                    '{} had {} flowers, now they have {}'.format(user.display_name, json_data[user_id], count))
                json_data[user_id] = int(count)
            except KeyError:
                return
            except ValueError:
                await self.bot.say('{} is not an integer!'.format(count))

        with open('flowers.json', 'w') as json_file:
            json_file.write(json.dumps(json_data, indent=2))


def setup(bot):
    bot.add_cog(Flowers(bot))
