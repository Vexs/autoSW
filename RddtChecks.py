import discord
from discord.ext import commands
from utils import checks
import aiohttp

class RddtChecks():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_botbanned()
    async def checkrddt(self,usr='Test'):
        """Checks to see if an string is a valid reddit user account! Only returns true if combined karma is over 10!"""
        with aiohttp.ClientSession() as session:
            async with session.get(r'https://www.reddit.com/user/{}/about.json'.format(usr)) as r:
                if r.status == 200:
                    js = await r.json()
                    totalkarma = int(js['data']['comment_karma']) + int(js['data']['link_karma'])
                    if totalkarma > 10:
                        await self.bot.say('{} is a dirty redditor! And they have {} karma!'.format(usr, totalkarma))
                    else:
                        await self.bot.say('{} is probably not a redditor.'.format(usr))
                else:
                    await self.bot.say('{} is probably not a redditor.'.format(usr))

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def longgetrddt(self,ctx):
        redditors = []
        for memb in list(ctx.message.server.members):
            usr = memb.display_name
            with aiohttp.ClientSession() as session:
                async with session.get(r'https://www.reddit.com/user/{}/about.json'.format(usr)) as r:
                    try:
                        js = await r.json()
                        if 'error' not in js:
                            print(usr)
                            redditors.append((usr, int(js['data']['comment_karma']) + int(js['data']['link_karma'])))
                    except:
                        print('error on {}'.format(usr))
        redditors = sorted(redditors, key=lambda x: x[1], reverse=True)
        redditorsay = 'The following {} people are redditors!\n'.format(len(redditors))
        for redditor in redditors:
            redditorsay = "{}**{}** has **{}** karma!\n".format(redditorsay, redditor[0], str(redditor[1]))
            if len(redditorsay) > 1900:
                await self.bot.say(redditorsay)
                redditorsay = ''
        await self.bot.say(redditorsay)



def setup(bot):
    bot.add_cog(RddtChecks(bot))