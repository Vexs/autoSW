import discord
from discord.ext import commands
from utils import checks
import basc_py4chan
import re
from utils import chanUtils

class ChanTools():
    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def thread(self):
        """Gets the current /tfg/ thread"""
        vg = basc_py4chan.Board('vg')
        threads = vg.get_all_threads()
        for thr in threads:
            if '/tfg/' in thr.topic.subject:
                await self.bot.say(vg.get_thread(thr.id).url)
                break


    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def getlatest(self,cxt):
        """Gets the most recent post in the thread!"""
        thr = chanUtils.getthread()
        post = thr.posts[-1]
        em = chanUtils.posttoembed(post)
        await self.bot.send_message(cxt.message.channel, embed=em)


    @commands.command(pass_context=True)
    @checks.is_owner()
    async def postthread(self,cxt, count=10):
        """Vex only! Posts N many posts from the current thread. Really don't know why I haven't removed this."""
        thr = chanUtils.getthread()
        for p in range(1, count + 1):
            post = thr.posts[p]
            await self.bot.send_message(cxt.message.channel, embed=chanUtils.posttoembed(post))


    @commands.command()
    @checks.is_owner()
    async def postsafter(self,idin):
        """Vex only! Returns all posts after a post"""
        thread = chanUtils.getthread()
        for position, post in enumerate(thread.posts):
            if post.post_id == int(idin):
                for pos in thread.posts[position + 1:]:
                    await self.bot.say(embed=chanUtils.posttoembed(pos))
                break


    @commands.command()
    @checks.is_botbanned()
    async def getquotes(self,idin):
        """Usage: getquotes <postid>. Returns all posts quoted by a post."""
        thr = chanUtils.getthread()
        for post in thr.posts:
            if str(post.post_id) == idin:
                await self.bot.say('Getting posts that post {} quotes! \n ```{}```'.format(idin, post.text_comment))
                for quote in re.finditer('>>\d{9}', post.text_comment):
                    for pos in thr.posts:
                        if str(pos.post_id) == quote.group(0).strip('>'):
                            await self.bot.say(embed=chanUtils.posttoembed(pos))
                break
        else:
            await self.bot.say('Post not found!')


    @commands.command()
    @checks.is_botbanned()
    async def getpost(self,idin):
        """Usage: Getpost <postid>. Returns the post given in postid."""
        thr = chanUtils.getthread()
        for post in thr.posts:
            if str(post.post_id) == idin:
                await self.bot.say(embed=chanUtils.posttoembed(post, False))
                break
        else:
            await self.bot.say('Post not found!')

def setup(bot):
    bot.add_cog(ChanTools(bot))