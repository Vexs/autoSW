import asyncio
import functools

import discord
from discord.ext import commands
from utils import checks
import re
import youtube_dl
import functools
import aiohttp
import datetime
import os
import json


async def create_ytdl_download_player(self, voice_client, song, *, opts=None, **kwargs):
    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, song, download=False)
    info = await self.loop.run_in_executor(None, func)

    json_data = self.json_data

    if "entries" in info:
        info = info['entries'][0]

    download_url = info['url']

    if info.get('duration') > 3600:
        raise Exception('Song is too long! Please limit your songs to one hour!')

    if info['id'] not in json_data.keys() or info['id']+'.mp3' not in os.listdir('music_files/'):
        # # func = functools.partial(ydl.download, song)
        # func = functools.partial(ydl.extract_info, song)
        # await self.loop.run_in_executor(None, func)
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                with open('music_files/{}.mp3'.format(info['id']), 'wb') as file:
                    file.write(await resp.read())


    json_data[info['id']] = {'title': info['title'], 'life': 101}

    #things_to_pop = []
    for key in json_data.copy().keys():
        json_data[key]['life'] -= 1
        if json_data[key]['life'] <= 0:
            print('purging {}'.format(key))
            json_data.pop(key, None)
            try:
                os.remove('music_files/{}.mp3'.format(key))
            except FileNotFoundError:
                print('Unable to find {}.mp3'.format(key))
            #things_to_pop.append(key)

    #for key in things_to_pop:
    #    json_data.pop(key, None)

    with open('music_files/music.json', 'w') as json_file:
        json_file.write(json.dumps(json_data, indent=2))

    # for file_name in os.listdir('music_files/'):
    #    if info['id'] in file_name:
    #        break
    # else:
    #    async with aiohttp.ClientSession() as session:
    #        async with session.get(download_url) as resp:
    #            with open('music_files/{}.mp3'.format(info['id']), 'wb') as file:
    #                file.write(await resp.read())

    player = voice_client.create_ffmpeg_player('music_files/{}.mp3'.format(info['id']), **kwargs)

    player.download_url = download_url
    player.info = info
    player.yt = ydl
    player.url = info.get('url')
    player.id = info.get('id')
    player.uploader = info.get('uploader')
    player.duration = info.get('duration')

    if 'twitch' in info.get('url'):
        # twitch has 'title' and 'description' sort of mixed up.
        player.title = info.get('description')
        player.description = None
    else:
        player.title = info.get('title')
        player.description = info.get('description')

    date = info.get('upload_date')
    if date:
        try:
            date = datetime.datetime.strptime(date, '%Y%M%d').date()
        except ValueError:
            date = None

    player.upload_date = date
    return player


class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player
        self.url = player.url
        description_string = 'Uploaded by {0.uploader}'
        duration = self.player.duration
        if duration:
            description_string += ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        description_string = description_string.format(self.player, self.requester)

        self.embed = discord.Embed(title=player.title, description=description_string)
        self.embed.color = 0xE52D49
        self.embed.set_author(name='Requested by: ' + self.requester.display_name, icon_url=self.requester.avatar_url)
        self.embed.url = player.info['webpage_url']
        try:
            self.embed.set_image(url=player.info['thumbnails'][0]['url'])
        except KeyError:
            pass

        self.start_datetime = datetime.datetime.now()
        self.end_datetime = self.start_datetime + datetime.timedelta(seconds=player.duration)

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by **{1.display_name}**'
        duration = self.player.duration
        if duration:
            fmt += ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

    def time_remaining(self, current_time):
        return self.end_datetime - current_time


class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            try:
                await self.bot.send_message(self.current.channel, embed=self.current.embed)
            except discord.Forbidden:
                await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()


class MusicTest:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.voice_states = {}
        with open('music_files/music.json') as json_file:
            json_data = json.load(json_file)
        self.json_data = json_data
        self.opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            #'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'outtmpl':'music_files/%(id)s.mp3',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'quiet': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except Exception:
                pass

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def join(self, ctx, *, channel: discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def play(self, ctx, *, song: str):
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return
        try:
            await self.bot.send_typing(ctx.message.channel)
            player = await create_ytdl_download_player(self, state.voice, song, opts=self.opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song."""
        if value > 100:
            value = 100
        elif value < 10:
            value = 10

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)

        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except Exception:
            pass

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        half the people in the channel need to vote for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return
        channel_member_count = len(state.voice.channel.voice_members) - 1
        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
        if voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= channel_member_count / 2:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say(
                    'Skip vote added, currently at [{}/{}]'.format(total_votes, channel_member_count / 2))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def adminskip(self, ctx):
        """Forces song skip. For admins"""
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return
        if ctx.message.author.server_permissions.manage_roles:
            await self.bot.say('Admin skipping song...')
            state.skip()

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def playing(self, ctx):
        """Shows info about the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            remaining_seconds = state.current.time_remaining(ctx.message.timestamp).seconds
            remaining_string = '{}m {}s'.format(remaining_seconds // 60, remaining_seconds % 60)
            await self.bot.say('Now playing {}, [remaining: {}] [skips: {}]'.format(state.current,
                                                                                     remaining_string,
                                                                                     skip_count))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    async def playlist(self, ctx):
        """Shows the current playlist"""
        state = self.get_voice_state(ctx.message.server)
        playlist = '**Current:** {}\n'.format(str(state.current))
        if len(playlist) != 0:
            safe_queue = list(state.songs._queue)
            for number, song in enumerate(safe_queue):
                nextline = '**{}**, {}\n'.format(number + 1, str(song))
                if (len(playlist) + len(nextline)) < 2048:
                    playlist += nextline
                else:
                    break
        await self.bot.say(playlist)

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def updateCache(self, ctx):
        for file_name in os.listdir('music_files/'):
            self.json_data[os.path.splittext('music_files/{}'.format(file_name))[0]] = {'title':file_name, 'life':100}
        with open('music_files/music.json', 'w') as json_file:
            json_file.write(json.dumps(self.json_data, indent=2))


def setup(bot):
    bot.add_cog(MusicTest(bot))
