import inspect
import aiohttp
import discord
from discord.ext import commands
from utils import checks
import os
import re

class AdminTools():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_owner()
    async def botsay(self,chan, *, msg):
        await self.bot.send_message(self.bot.get_channel(chan), msg)

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def banned(self,ctx,msgtoscan):
        """Bans(mutes) everyone who has posted in the last N<=50 messages. Alternatively, you can mention people and that works too. Admin only. """
        bannedrole = discord.utils.get(ctx.message.server.roles, name='banned')
        count = 0
        try:
            msgtoscan = int(msgtoscan)
            if msgtoscan > 50:
                msgtoscan = 50
            async for msg in self.bot.logs_from(ctx.message.channel, limit=msgtoscan):
                try:
                    if msg.author != ctx.message.author and msg.author != ctx.message.server.me:
                        if bannedrole not in msg.author.roles and not msg.author.server_permissions.manage_roles:
                            await self.bot.add_roles(msg.author, bannedrole)
                            count += 1
                except discord.Forbidden:
                    pass
            await self.bot.say('Banned {} people'.format(count))
        except ValueError:
            for mem in ctx.message.mentions:
                if bannedrole not in mem.roles:
                    await self.bot.add_roles(mem, bannedrole)
                    count += 1
            await self.bot.say('Banned {} people'.format(count))

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def unbanned(self,ctx):
        """Unbans everyone. Admin only, fuck you."""
        bannedrole = discord.utils.get(ctx.message.server.roles, name='banned')
        count = 0
        if len(ctx.message.mentions) == 0:
            for mem in ctx.message.server.members:
                if bannedrole in mem.roles:
                    await self.bot.remove_roles(mem, bannedrole)
                    count += 1
        else:
            for mem in ctx.message.mentions:
                if bannedrole in mem.roles:
                    await self.bot.remove_roles(mem, bannedrole)
                    count += 1

        await self.bot.say('Unbanned {} people'.format(count))

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def clean(self,ctx,count=100):
        """Cleans a number of posts from a channel.
    If anyone is mentioned in the clean, it will clean just them."""
        if not ctx.message.mentions:
            deleted = await self.bot.purge_from(ctx.message.channel,limit=count)
        else:
            def check(message):
                return message.author in ctx.message.mentions

            deleted = await self.bot.purge_from(ctx.message.channel,limit=count,check=check)
        await self.bot.say('Deleted {} messages!'.format(len(deleted)),delete_after=10)



    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code : str):
        """Evaluates code."""
        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'server': ctx.message.server,
            'channel': ctx.message.channel,
            'author': ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await self.bot.say(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await self.bot.say(python.format(result))


    @commands.command(pass_context=True)
    @checks.is_owner()
    async def upload(self,ctx,*,filename:str=None):
        def check(reaction, user):
            if user.id != ctx.message.author.id:
                return False
            return True
        try:
            file_url = ctx.message.attachments[0]['url']
        except IndexError:
            await self.bot.say('No file uploaded!')
            return

        if filename is None:
            filename = ctx.message.attachments[0]['filename']
        if '/' or '\\' in filename:
            filename = re.split(r"/|\\",filename)

        reaction_msg = await self.bot.say('File URL is {}, with filename {}, is this okay? ✅/❌'.format(file_url,filename[-1]),delete_after=60)
        await self.bot.add_reaction(reaction_msg, '✅')
        await self.bot.add_reaction(reaction_msg, '❌')
        resp = await self.bot.wait_for_reaction(['✅', '❌'], message=reaction_msg, check=check,timeout=60)
        if resp is None:
            await self.bot.say('Timed out! Aborting!', delete_after=90)
        elif resp.reaction.emoji == '❌':
            await self.bot.say('Aborting!', delete_after=90)
        elif resp.reaction.emoji == '✅':
            try:
                await self.bot.clear_reactions(reaction_msg)
            except discord.Forbidden:
                pass
            try:
                file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),*filename)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.makedirs(os.path.dirname(file_path))
                with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as resp:
                        content = await resp.read()
                with open(file_path,'wb') as f:
                    f.write(content)

                await self.bot.say('Successfully uploaded {}!'.format(filename[-1]), delete_after=30)
            except Exception as e:
                await self.bot.say(e)
        await self.bot.delete_message(ctx.message)



def setup(bot):
    bot.add_cog(AdminTools(bot))