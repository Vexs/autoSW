import discord
from discord.ext import commands
import re
from utils import checks
import dice


class ServerTools():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def quote(self,cxt, quoteid):
        """Quotes a message! Usage: &quote <message ID>"""
        message = next((x for x in self.bot.messages if x.id == quoteid), None)
        regex = re.compile('(?P<url>https?://[^\s]+(jpg|png))')
        em = discord.Embed(description=message.content, colour=0x789922, timestamp=message.timestamp)
        if re.match(regex, message.content) is not None:
            em.set_image(re.match(regex, message.content))
        em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def roleme(self,ctx, *, role):
        """Sets your NA/EU role. Usage: &roleme <na/eu/shitposting>, or &roleme remove to remove all roles"""
        rolenames = ['NA','EU','shitposting']
        roles = []
        for r in rolenames:
            try:
                roles.append(discord.utils.get(ctx.message.server.roles,name=r))
            except discord.NotFound:
                await print('Role {} not found!'.format(r))
        if role.lower() == 'remove':
            for r in roles:
                await self.bot.remove_roles(ctx.message.author, r)
            await self.bot.say('Role(s) removed!')
        else:
            for r in roles:
                if r.name.lower() == role.lower():
                    await self.bot.add_roles(ctx.message.author, r)
                    await self.bot.say('Role "{}" added!'.format(r.name))
                    break


    @commands.command()
    @checks.is_botbanned()
    async def searchusers(self,name):
        """Usage: &searchusers <username>. Returns the origin profile search page for that username."""
        await self.bot.say('https://www.origin.com/usa/en-us/search?searchString={}&category=people'.format(name))

    @commands.command()
    @checks.is_botbanned()
    @commands.cooldown(1,30,type=commands.BucketType.user)
    async def roll(self,*,dice_string):
        """Rolls XdY dice.
Advanced functions:
Supports basic arithmatic (1d6 + 5)
Selecting the n lowest/highest roles can be done with ^ and v, (6d6^3) uses only the 3 highest rolls
You can also add different dice (2d8 + 1d20)"""
        if len(dice_string) < 10:
            dice_roll = dice.roll(dice_string)
            try:
                dice_sum_string = str(sum(dice_roll))
                if len(dice_sum_string) > 10:
                    dice_sum_string = '{:.10e}'.format(sum(dice_roll))
            except TypeError:
                dice_sum_string = str(dice_roll)
                if len(dice_sum_string) > 10:
                    dice_sum_string = '{:.10e}'.format(dice_roll)

            dice_roll_string = 'Rolling **{}** \n =**{}**'.format(dice_string, dice_sum_string)
            await self.bot.say(dice_roll_string)
        else:
            await self.bot.say('Quit trying to fuck up the bot')

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def whosplaying(self, ctx, *, game=None):
        """Tells you how many people are playing <game>
Not providing a game will give you the top 10 played games"""
        game_name = game
        if game_name == 'games' or game_name is None:
            game_dict = {}
            for m in ctx.message.server.members:
                if m.game is not None:
                    game_dict[m.game.name] = game_dict.get(m.game.name, 0) + 1
            sorted_dict = sorted(game_dict.items(), key=(lambda x: x[1]), reverse=True)
            say_string = 'Games being played: \n' + '\n'.join(['**{}** people playing **{}**'.format(value, key) for (key, value) in sorted_dict][:10])
            await self.bot.say(say_string)

        else:
            game_list = []
            for x in ctx.message.server.members:
                if x.game is not None:
                    if game_name.lower() in x.game.name.lower():
                        game_list.append('**{}**'.format(x.display_name))
            await self.bot.say('There are **{}** people playing **{}**:\n{}'.format(len(game_list), game_name,'\n'.join(game_list)))

    @commands.command(pass_context=True)
    async def admincheck(self,ctx,user_to_check:discord.Member):
        """Checks if someone has admin permissions. """
        user = user_to_check
        total_perms = [user.permissions_in(x) for x in ctx.message.server.channels]
        for p in total_perms:
            if p.administrator or p.ban_members or p.kick_members or p.manage_messages or p.manage_nicknames or p.manage_roles:
                await self.bot.say('{} has admin permissions!'.format(user_to_check.display_name))
                return
        await self.bot.say('{} does not have admin permissions.'.format(user_to_check.display_name))


def setup(bot):
    bot.add_cog(ServerTools(bot))