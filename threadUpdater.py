import discord
import asyncio
import basc_py4chan
from utils import chanUtils
import re


def get_thread(board, thread_identifier):
    board = basc_py4chan.Board(board)
    return next(x for x in board.get_all_threads() if thread_identifier in x.topic.subject)

async def last_post_id_get(bot, channel):
    async for message in bot.logs_from(channel, limit=100):
        if message.author.id == bot.user.id:
            if message.embeds:
                try:
                    return int(re.search(r'No\. (\d+)', message.embeds[0]['title']).group(1))
                except:
                    pass
    return None


async def update_thread(bot, board_name, thread_name, general_channel_id, mirror_channel_id):
    await bot.wait_until_ready()

    general_channel = discord.Object(id=general_channel_id)
    mirror_channel = discord.Object(id=mirror_channel_id)

    last_post_id = await last_post_id_get(bot, mirror_channel)

    thread = await bot.loop.run_in_executor(None, get_thread, board_name, thread_name)
    await bot.loop.run_in_executor(None, thread.update)

    if not any(x for x in thread.posts if x.post_id == last_post_id):
        last_post_id = None

    while not bot.is_closed:
        if last_post_id is not None:
            new_posts = sum(1 for x in thread.all_posts if x.post_id > last_post_id)
            last_post_id = None
        else:
            new_posts = await bot.loop.run_in_executor(None, thread.update)

        if new_posts == 0:
            old_url = thread.url
            old_time = thread.topic.datetime
            thread = await bot.loop.run_in_executor(None, get_thread, board_name, thread_name)

            if old_url != thread.url and old_time < thread.topic.datetime:
                await bot.send_message(general_channel, "New thread at: " + thread.url)

        for post in thread.posts[len(thread.posts) - new_posts:]:
            await bot.send_message(mirror_channel, embed=chanUtils.posttoembed(post))

        await asyncio.sleep(60)


class ThreadUpdater:
    """"""

    def __init__(self, bot):
        self.bot = bot
        self.loop = self.bot.loop
        self.thread_update_task = self.bot.loop.create_task(update_thread(self.bot, 'vg', 'Titanfall General',
                                                                     '298667118810103808', '275869654919151617'))

    def __unload(self):
        self.thread_update_task.cancel()


def setup(bot):
    bot.add_cog(ThreadUpdater(bot))
