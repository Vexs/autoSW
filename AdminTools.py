import inspect
import aiohttp
import discord
from discord.ext import commands
from utils import checks
import os
import re
import asyncio
import io

regex = re.compile(r"^\*?un(.{1,5})s\b", re.IGNORECASE)

async def unzips(self, message):
    search = re.match(regex, message.content)
    if search is not None:
        bannedrole = discord.utils.get(message.server.roles, name='banned')
        if bannedrole not in message.author.roles:
            await self.bot.send_message(message.channel, '*re{}s*'.format(search.group(1)))
            await self.bot.add_roles(message.author, bannedrole)
            await asyncio.sleep(60)
            await self.bot.remove_roles(message.author, bannedrole)

class AdminTools():
    def __init__(self, bot):
        self.bot = bot
        self.purged_messages = []

    @commands.command()
    @checks.is_owner()
    async def botsay(self, chan, *, msg):
        await self.bot.send_message(self.bot.get_channel(chan), msg)

    async def on_message(self, message):
        await unzips(self, message)

    async def on_message_edit(self, before, message):
        await unzips(self, message)

    @commands.command(pass_context=True, aliases=['zipped'])
    @checks.mod_or_permissions(manage_roles=True)
    async def banned(self, ctx, msgtoscan):
        """Bans everyone who has posted in the last N<=50 messages. Alternatively, you can mention people and that works too. Admin only. """
        bannedrole = discord.utils.get(ctx.message.server.roles, name='banned')
        people_to_banned = []

        try:
            msgtoscan = int(msgtoscan)
            if msgtoscan > 50:
                msgtoscan = 50

            async for msg in self.bot.logs_from(ctx.message.channel, limit=msgtoscan):
                if msg.author != ctx.message.author and msg.author != ctx.message.server.me:
                    if bannedrole not in msg.author.roles and not msg.author.server_permissions.manage_roles:
                        if msg.author not in people_to_banned:
                            people_to_banned.append(msg.author)
        except ValueError:
            for mem in ctx.message.mentions:
                if bannedrole not in mem.roles:
                    people_to_banned.append(mem)

        for member in people_to_banned:
            try:
                await self.bot.add_roles(member, bannedrole)
            except discord.Forbidden:
                pass

        await self.bot.say('{} {} people'.format('Zipped' if ctx.invoked_with == 'zipped' else 'Banned',
                                                 len(people_to_banned)))

        await asyncio.sleep(3500)

        unbanned_list = []
        for member in people_to_banned:
            if bannedrole in member.roles:
                await self.bot.remove_roles(mem, bannedrole)
                unbanned_list.append(member.name)
        if len(unbanned_list) != 0:
            await self.bot.send_message(discord.Object(id='250776212383727616'),
                                        '{}, I unbanned {}'.format(ctx.message.author.mention,
                                                                   ', '.join(unbanned_list)))

    @commands.command(pass_context=True, aliases=['unzipped'])
    @checks.mod_or_permissions(manage_roles=True)
    async def unbanned(self, ctx):
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

        await self.bot.say('{} {} people'.format('Unzipped' if ctx.invoked_with == 'unzipped' else 'Unbanned', count))

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def clean(self, ctx, count=100):
        """Cleans a number of posts from a channel.
    If anyone is mentioned in the clean, it will clean just them."""
        if not ctx.message.mentions:
            self.purged_messages = await self.bot.purge_from(ctx.message.channel, limit=count)
        else:
            def check(message):
                return message.author in ctx.message.mentions

            self.purged_messages = await self.bot.purge_from(ctx.message.channel, limit=count, check=check)

        await self.bot.say('Deleted {} messages!'.format(len(self.purged_messages)), delete_after=10)
        channel = self.bot.get_channel('298251828850589698')

        purged_messages = self.purged_messages
        purged_messages.reverse()
        file = io.BytesIO()
        log_list = []
        for msg in purged_messages:
            log_list.append('[{}] <{}>: {}'.format(msg.timestamp.strftime('%F %H:%M'),msg.author.display_name,
                                                 msg.clean_content))
            if msg.embeds:
                for embed in msg.embeds:
                    log_list.append('Embed:')
                    for key, value in embed.items():
                        log_list.append('{} : {}'.format(key, value))

        file.write(bytes('\r\n'.join(log_list),'utf-8'))
        file.seek(0)
        await self.bot.send_file(channel, file, filename='logs.txt', content='{} Deleted {} messages in {}'.format(
            ctx.message.author.display_name, len(self.purged_messages), ctx.message.channel.name))


    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code: str):
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
    async def upload(self, ctx, *, filename: str = None):
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
            filename = re.split(r"/|\\", filename)

        reaction_msg = await self.bot.say(
            'File URL is {}, with filename {}, is this okay? ✅/❌'.format(file_url, filename[-1]), delete_after=60)
        await self.bot.add_reaction(reaction_msg, '✅')
        await self.bot.add_reaction(reaction_msg, '❌')
        resp = await self.bot.wait_for_reaction(['✅', '❌'], message=reaction_msg, check=check, timeout=60)
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
                file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), *filename)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.makedirs(os.path.dirname(file_path))
                with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as resp:
                        content = await resp.read()
                with open(file_path, 'wb') as f:
                    f.write(content)

                await self.bot.say('Successfully uploaded {}!'.format(filename[-1]), delete_after=30)
            except Exception as e:
                await self.bot.say(e)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def mod(self, ctx):
        mod_role = discord.utils.get(ctx.message.server.roles, name='"MOD"')
        count = 0
        for member in ctx.message.server.members:
            if member.status is not discord.Status.offline:
                await self.bot.add_roles(member, mod_role)
                count += 1
        await self.bot.say('I did it {} times'.format(count))

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def demod(self, ctx):
        mod_role = discord.utils.get(ctx.message.server.roles, name='"MOD"')
        count = 0
        for member in ctx.message.server.members:
            if mod_role in member.roles:
                await self.bot.remove_roles(member, mod_role)
                count += 1
        await self.bot.say('I did it {} times'.format(count))


def setup(bot):
    bot.add_cog(AdminTools(bot))
