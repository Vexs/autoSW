import discord
from discord.ext import commands
from utils import checks
import basc_py4chan
import re
from utils import chanUtils
import aiohttp
import io
import cv2

def posttoembed(post, thread_id, board_name, thumbnail=True):
    rawcomment = post.comment
    textcomment = post.text_comment
    innermatches = re.findall(r'<a href="#p(.*?)" class="quotelink">', rawcomment)
    outermatches = re.findall(r'<a href="/vg/thread/[0-9]{9}#p([0-9]{9})', rawcomment)
    outermatchurl = re.findall(r'<a href="/(.*?)" class="quotelink">', rawcomment)
    for m in innermatches:
        textcomment = textcomment.replace('>>{}'.format(m),
                                          '[>>{id}](http://boards.4chan.org/{boardname}/thread/{threadid}#p{id})'.format(id=m,threadid=thread_id,boardname=board_name))
    for (i, m) in enumerate(outermatches):
        textcomment = textcomment.replace('>>{}'.format(m),
                                          '[>>{}](http://boards.4chan.org/{}/thread/{})'.format(m, board_name, outermatchurl[i]))

    if post.has_file:
        textcomment += '\n\n[File URL]({})'.format(post.file.file_url)

    if len(textcomment) > 2047:
        textcomment = textcomment[:2036] + '**...(cutoff)**'
    em = discord.Embed(description=textcomment, colour=0xD6DAF0, timestamp=post.datetime,
                       title='No. {}'.format(str(post.post_id)), url=post.url)
    em.set_author(name=post.name + ('#' + post.tripcode if post.tripcode is not None else ''))
    if post.has_file:
        if post.spoiler:
            em.set_thumbnail(url=r'http://s.4cdn.org/image/spoiler-v1.png')
        elif thumbnail:
            em.set_thumbnail(url=post.file.thumbnail_url.replace('http://', 'https://'))
        else:
            em.set_image(url=post.file.file_url.replace('http://', 'https://'))
        em.set_footer(text=post.file.filename_original)
    return em

async def chan_url_embed(self, message):
    if message.author.id == self.bot.user.id:
        return
    search = re.search(self.url_regex, message.content)
    if search is None:
        return
    board = basc_py4chan.Board(search.group(1))
    try:
        board.title
    except KeyError:
        return
    if board.is_worksafe or board.is_worksafe != message.channel.name.startswith('nsfw'):
        thread = board.get_thread(search.group(2))
        if thread is None:
            return
        if search.group(3) is not None:
            post = next((post for post in thread.posts if post.post_id == int(search.group(3))), None)
            if post is None:
                return
            await self.bot.send_message(message.channel, embed=posttoembed(post, search.group(2), search.group(1)))
        else:
            await self.bot.send_message(message.channel,
                                        embed=posttoembed(thread.topic, search.group(2), search.group(1)))


class ChanTools():
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = re.compile(r'https?:\/\/boards\.4chan\.org\/([a-z0-9]{1,5})\/thread\/(\d+)(?:#p(\d+))?')
        self.webm_regex = re.compile(r'(https?:\/\/i.4cdn.org\/[a-z0-9]{1,5}\/\d+.webm)')


    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def thread(self):
        """Gets the current /tfg/ thread"""
        vg = basc_py4chan.Board('vg')
        threads = vg.get_all_threads()
        for thr in threads:
            if '/tfg/' in thr.topic.subject and 'titanfall' in thr.topic.subject.lower():
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



    async def on_message(self, message):
        await chan_url_embed(self, message)
        #search = re.search(self.webm_regex, message.content)
        #if search is None:
        #    return
        #url = search.group(1)
        #vidcap = cv2.VideoCapture(url)
        #success, image = vidcap.read()
        #imagefileobject = io.BytesIO()
        #cv2.imwrite('test.png', image)
        ##cv2.imwrite(imagefileobject, image)
        ##imagefileobject.seek(0)
        ##await self.bot.send_file(message.channel, fp=imagefileobject, filename='angry.png')


def setup(bot):
    bot.add_cog(ChanTools(bot))