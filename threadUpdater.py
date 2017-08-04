import discord
import asyncio
import basc_py4chan
import re
from discord.ext import commands
import datetime


def post_to_embed(post, thumbnail=True):
    thread_id_from_post = re.match(r'http://boards.4chan.org/vg/thread/([0-9]{9})#p', post.url).group(1)
    raw_comment = post.comment
    text_comment = post.text_comment
    inner_matches = re.findall(r'<a href="#p(.*?)" class="quotelink">', raw_comment)
    outer_matches = re.findall(r'<a href="/vg/thread/[0-9]{9}#p([0-9]{9})', raw_comment)
    outer_match_url = re.findall(r'<a href="/(.*?)" class="quotelink">', raw_comment)
    for m in inner_matches:
        text_comment = text_comment.replace('>>{}'.format(m),
                                            '[>>{id}](http://boards.4chan.org/vg/thread/{threadid}#p{id})'
                                            .format(id=m, threadid=thread_id_from_post))
    for (i, m) in enumerate(outer_matches):
        text_comment = text_comment.replace('>>{}'.format(m),
                                            '[>>{}](http://boards.4chan.org/vg/thread/{})'
                                            .format(m, outer_match_url[i]))

    if len(text_comment) > 2047:
        text_comment = text_comment[:2030] + '**...(cutoff)**'
    embed = discord.Embed(description=text_comment, colour=0xD6DAF0, timestamp=post.datetime,
                          title='No. {}'.format(str(post.post_id)), url=post.url)
    embed.set_author(name=post.name + ('#' + post.tripcode if post.tripcode is not None else ''))
    if post.has_file:
        if post.spoiler:
            embed.set_thumbnail(url=r'http://s.4cdn.org/image/spoiler-v1.png')
        elif thumbnail:
            embed.set_thumbnail(url=post.file.thumbnail_url.replace('http://', 'https://'))
        else:
            embed.set_image(url=post.file.file_url.replace('http://', 'https://'))
        embed.set_footer(text=post.file.filename_original)
    return embed


class AsyncChanThread:
    def __init__(self, bot: discord.ext.commands.bot, channel: discord.Channel, board: str,
                 thread_name: str):
        self.bot = bot
        self.channel = channel
        self.thread_name = thread_name
        self.board = board
        self.thread = None
        self.is_setup = False

    async def setup(self, get_last_post=False):
        self.thread = await self.get_thread(self.board, self.thread_name)
        if self.thread is None:
            await asyncio.sleep(5)
            self.thread = await self.get_thread(self.board, self.thread_name)
            if self.thread is None:
                print('Thread not found')
                return await self.bot.send_message(self.channel, 'Thread not found!')
        self.is_setup = True
        await self.update()
        if get_last_post:
            last_post = await self.get_last_post_id(self.channel)
            print('found last post: ' + str(last_post))
            if last_post:
                #posts = await self.all_posts()
                await self.update()
                posts = self.thread.posts
                if any(x for x in posts if x.post_id == last_post):
                    post_list = [x for x in posts if x.post_id > last_post]
                    print('Found last post {}, sent {} posts'.format(last_post, len(post_list)))
                    await self.send_posts(post_list)


    async def get_last_post_id(self, channel):
        regex = re.compile(r'No\. (\d+)')
        async for message in self.bot.logs_from(channel, limit=100):
            if message.author.id == self.bot.user.id:
                if message.embeds:
                    try:
                        search = re.search(regex, message.embeds[0]['title'])
                        if search is None:
                            pass
                        if search.group(1) == '':
                            pass
                        return int(search.group(1))
                    except Exception:
                        pass
        return None

    async def update(self) -> int:
        if self.is_setup:
            try:
                return await self.bot.loop.run_in_executor(None, self.thread.update)
            except Exception as e:
                print('Exception in updating thread at: ' + str(datetime.datetime.utcnow()))
                print(e)
                return 0

    async def get_thread(self, board, thread_name) -> basc_py4chan.Thread:

        def sync_get_thread(board, thread_identifier):
            board = basc_py4chan.Board(board)
            return next((x for x in board.get_all_threads() if thread_identifier in x.topic.subject), None)

        try:
            thread = await self.bot.loop.run_in_executor(None, sync_get_thread, board, thread_name)
            if thread is None:
                return self.thread
            return thread
        except Exception as e:
            print('Exception in getting thread at: ' + str(datetime.datetime.utcnow()))
            print(e)
            return self.thread

    async def get_new_posts(self):
        if not self.is_setup:
            return
        new_post_count = await self.update()
        return self.thread.posts[len(self.thread.posts) - new_post_count:]

    async def thread_update(self):
        if self.thread.archived:
            print('Thread Archived')
            self.thread = await self.get_thread(self.board, self.thread_name)
            await self.update()
            return self.thread.posts[1:]
        new_posts = await self.get_new_posts()
        if len(new_posts) == 0 or self.thread.bumplimit:
            new_thread = await self.get_thread(self.board, self.thread_name)
            if new_thread.url != self.thread.url:
                print('New thread!')
                await self.bot.send_message(
                    discord.Object(id='298667118810103808'), 'New thread at {}'.format(new_thread.url))
                self.thread = new_thread
                await self.update()
                return self.thread.posts[1:]
            return []
        return self.thread.posts[len(self.thread.posts) - len(new_posts):]

    async def send_posts(self, posts):
        for post in posts:
            await self.bot.send_message(self.channel, embed=post_to_embed(post))

    async def do_update(self):
        posts = await self.thread_update()
        if posts:
            await self.send_posts(posts)


class ThreadUpdater:
    async def thread_update_task(self):
        await self.bot.wait_until_ready()
        # for thread in self.threads:
        #    await thread.setup()
        # while not self.bot.is_closed:
        #    for thread in self.threads:
        #        await thread.do_update()
        await self.thread.setup(get_last_post=True)
        while not self.bot.is_closed:
            await self.thread.do_update()
            await asyncio.sleep(60)

    def __init__(self, bot):
        self.bot = bot
        self.loop = self.bot.loop
        channels = self.bot.get_all_channels()
        self.thread = AsyncChanThread(self.bot, discord.utils.get(channels, id='275869654919151617'), 'vg',
                                  '/tfg/')

        self.task = self.bot.loop.create_task(self.thread_update_task())

    def __unload(self):
        self.task.cancel()


def setup(bot):
    bot.add_cog(ThreadUpdater(bot))
