import asyncio
import discord
from discord.ext import commands
from utils import checks


def music_command_channel_check(message):
    return message.channel.id == '296815183299477505'

def music_command_channel():
    return commands.check(lambda ctx: music_command_channel_check(ctx.message))

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by **{1.display_name}**'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
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
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Music:
    """Music related commands.
    Code mostly by Danny.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

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
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    @music_command_channel()
    async def join(self, ctx, *, channel : discord.Channel):
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
    @music_command_channel()
    @commands.cooldown(1,120,type=commands.BucketType.user)
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
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    @checks.is_botbanned()
    @music_command_channel()
    async def play(self, ctx, *, song : str):
        """Plays a song.
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            #if len(state.songs._queue) != 0:
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @play.error
    async def play_error(self,error,ctx):
        if isinstance(error,commands.CommandOnCooldown):
            if ctx.message.author.server_permissions.manage_roles:
                await ctx.invoke(ctx.command, *ctx.args[2:], **ctx.kwargs)
                return
            await self.bot.say(error)
        else:
            await self.bot.say(error)


    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    @music_command_channel()
    async def volume(self, ctx, value : int):
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
    @music_command_channel()
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)

        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    @music_command_channel()
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    #@checks.mod_or_permissions(manage_roles=True)
    @checks.is_botbanned()
    @music_command_channel()
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
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    @music_command_channel()
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        half the people in the channel need to vote for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return
        channel_member_count = len(state.voice.channel.voice_members)-1
        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
        if voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= channel_member_count/2:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/{}]'.format(total_votes,channel_member_count/2))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_roles=True)
    @music_command_channel()
    async def adminskip(self,ctx):
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
    @music_command_channel()
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_botbanned()
    @music_command_channel()
    async def playlist(self,ctx):
        """Shows the current playlist"""
        state = self.get_voice_state(ctx.message.server)
        playlist = '**Current:** {}\n'.format(str(state.current))
        if len(playlist) != 0:
            safe_queue = list(state.songs._queue)
            for number,song in enumerate(safe_queue):
                nextline = '**{}**, {}\n'.format(number,str(song))
                if (len(playlist)+ len(nextline))<2048:
                    playlist = playlist + nextline
                else:
                    break
        await self.bot.say(playlist)





def setup(bot):
    bot.add_cog(Music(bot))
