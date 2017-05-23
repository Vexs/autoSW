from discord.ext import commands
from difflib import Differ
import discord
import asyncio
from utils.checks import mod_or_permissions


class logs:
    """"""

    def __init__(self, bot):
        self.bot = bot
        self.last_purged_messages = []
        self.purged_messages_id = []

    async def on_message_delete(self, message):
        if message.author == message.server.me:
            return
        if message.content == self.bot.command_prefix + 'pick':
            return
        if self.last_purged_messages != self.bot.get_cog('AdminTools').purged_messages:
            self.last_purged_messages = self.bot.get_cog('AdminTools').purged_messages
            self.purged_messages_id = [x.id for x in self.bot.get_cog('AdminTools').purged_messages]
        if message.id in self.purged_messages_id:
            return
        channel = self.bot.get_channel('298251828850589698')
        if message.attachments:
            try:
                message.attachments[0]['height']
                file_string = 'with image {} '.format(message.attachments[0]['filename'])
            except KeyError:
                file_string = 'with file {} '.format(message.attachments[0]['filename'])
        else:
            file_string = ''
        msg = '**{}**\'s ({}) message {}was deleted in {}' \
            .format(message.author.display_name, message.author.id, file_string, message.channel.name)
        if message.content:
            msg += ': '
            embed = discord.Embed(description=message.content)
        else:
            embed = None
        await self.bot.send_message(channel, content=msg, embed=embed)

    def diffHighlight(self, s1, s2):
        l1 = s1.split(' ')
        l2 = s2.split(' ')
        dif = list(Differ().compare(l1, l2))
        return " ".join(['[' + i[2:] + ']()' if i[:1] == '+' else i[2:] for i in dif if not i[:1] in '-?'])
        # dif = Differ().compare('a b c'.split(), 'a d c'.split())
        # list(dif) = ['  a', '- b', '+ d', '  c']
        # '[' + i[2:] + ']()' if i[:1] == '+' || if first char is +, it's an addition, so put it in []() for highlighting.
        # else i[2:] for i in dif if not i[:1] in '-?' || otherwise, return the rest of the stirng as long as it's not marked with an -, signifying remval

    async def on_message_edit(self, before, after):
        if before.author != before.server.me and before.content != after.content:
            channel = self.bot.get_channel('298251828850589698')
            msg = '**{}** ({})edited a message in {}:'.format(before.author.display_name, before.author.id,
                                                              before.channel.name)
            before_highlighted = self.diffHighlight(after.content, before.content)
            after_highlighted = self.diffHighlight(before.content, after.content)

            eb = discord.Embed(timestamp=after.timestamp)
            eb.add_field(name='Before:', value=before_highlighted[:1000], inline=False)
            if before_highlighted[1000:] != '':
                eb.add_field(name=u'\u200b', value=before_highlighted[1000:])

            eb.add_field(name='After:', value=after_highlighted[:1000], inline=False)
            if after_highlighted[1000:] != '':
                eb.add_field(name=u'\u200b', value=after_highlighted[1000:])

            await self.bot.send_message(channel, content=msg, embed=eb)

    async def on_member_ban(self, member):
        await self.bot.send_message(discord.Object(id='298667118810103808'),
                                    '<@{}> was banned!'.format(member.id))

    async def on_member_remove(self, member):
        await self.bot.send_message(discord.Object(id='298667118810103808'), '{} has left!'.format(member.name))

    async def on_member_join(self, member):
        await self.bot.send_message(discord.Object(id='298667118810103808'), 'Welcome to the TFG discord {}!'
                                    .format(member.name))


def setup(bot):
    bot.add_cog(logs(bot))
