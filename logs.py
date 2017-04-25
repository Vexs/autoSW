from discord.ext import commands
from difflib import Differ
import discord
import asyncio

class logs:
    """"""

    def __init__(self, bot):
        self.bot = bot

    async def on_message_delete(self, message):
        if message.author != message.server.me:
            channel = self.bot.get_channel('298251828850589698')
            msg = '**{}**\'s ({}) message was deleted in {}: '.format(message.author.display_name, message.author.id,
                                                                      message.channel.name)
            msg += "`{}`".format(message.content[:2048 - len(msg)])
            try:
                message.attachments[0]['url']
                embed = discord.Embed()
                embed.set_image(message.attachments[0]['url'])
                await self.bot.send_message(channel, msg, embed=embed)
            except IndexError:
                pass
                await self.bot.send_message(channel, msg)

    def diffHighlight(self,s1, s2):
        l1 = s1.split(' ')
        l2 = s2.split(' ')
        dif = list(Differ().compare(l1, l2))
        return " ".join(['[' + i[2:] + ']()' if i[:1] == '+' else i[2:] for i in dif if not i[:1] in '-?'])

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

    async def on_member_ban(self,member):
        await self.bot.send_message(discord.Object(id='298667118810103808'),
                               '<@{}> was banned!'.format(member.id))

    async def on_member_remove(self,member):
        await self.bot.send_message(discord.Object(id='298667118810103808'), '{} has left!'.format(member.name))

def setup(bot):
    bot.add_cog(logs(bot))