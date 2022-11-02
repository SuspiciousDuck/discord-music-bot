import discord
import time
import os
# youtube
from pytube import Playlist
import youtube_dl
import yt_dlp
# Commands
from discord.ext import commands
# Asyncio
import asyncio
import threading

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current_song = None
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'cookies': os.getcwd()+'cookies.txt',
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
    # Connect voice Channel
    @commands.command(case_insensitive=True)
    async def connect(self,ctx):
        voiceChannel = ctx.message.author.voice.channel
        if not voiceChannel:
            await ctx.send("You're not connected to a voice channel")
            return
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(voiceChannel)
        else:
            voice = await voiceChannel.connect()
        await ctx.send(f"Joined {voiceChannel}")

    # Help -> Command Manual
    @commands.command(name='help',case_insensitive=True)
    async def help(self,ctx):
        embed = discord.Embed(
            title = 'Command Manual',
            color = discord.Color.green()
        )
        # connect
        embed.add_field(name='!connect', value='connect voice channel', inline=False)
        # diconnect
        embed.add_field(name='!diconnect', value='diconnect voice channel', inline=False)
        # play
        embed.add_field(name='!play (url here)', value='play audio', inline=False)
        # stop
        embed.add_field(name='!stop', value='stop audio', inline=False)
        # pause
        embed.add_field(name='!pause', value='pause audio', inline=False)
        # resume
        embed.add_field(name='!resume', value='resume audio', inline=False)
        # skip
        embed.add_field(name='!skip', value='skip audio', inline=False)
        # clear
        embed.add_field(name='!clear', value='clear queue', inline=False)
        # songsinqueue
        embed.add_field(name='!songsinqueue', value='sends the queue', inline=False)
        #addplaylist
        embed.add_field(name='!addplaylist', value='adds a playlist to queue', inline=False)
        #ytsearch
        embed.add_field(name='!ytsearch', value='plays the first result of query', inline=False)
        #currentsong
        embed.add_field(name='!currentsong', value='sends the currently playing audio', inline=False)
        #restart
        embed.add_field(name='!restart', value='owner only, restarts commands to apply updates', inline=False)
        await ctx.send(embed=embed)

    # Play music
    @commands.command(case_insensitive=True)
    async def play(self,ctx, url: str,*args):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        duration = None

        #Streaming
        class YTDLSource(discord.PCMVolumeTransformer):
            def __init__(self, source, *, data, volume=0.5):
                super().__init__(source, volume)
                self.data = data
                self.title = data.get('title')
                self.url = data.get('url')
            @classmethod
            async def from_url(cls, url, *, loop=None, stream=False):
                youtube_dl.utils.bug_reports_message = lambda: ''
                ffmpeg_options = {
                    'options': '-vn',
                }
                ytdl = youtube_dl.YoutubeDL(self.ydl_opts)
                loop = loop or asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                if 'entries' in data:
                    # take first item from a playlist
                    data = data['entries'][0]
                filename = data['url'] if stream else ytdl.prepare_filename(data)
                return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            duration = ydl.extract_info(url,download=False)['duration']

        #get a stream
        audio = await YTDLSource.from_url(url=url, loop=self.bot.loop, stream=True)

        #check if bot is connected to voice channel
        if duration == None:
            await ctx.send("Couldn't retrieve duration data, try again or choose a different song.")
        if voice.is_connected() and duration != None:
            if not (True in args):
                self.queue.append(url)
            if not voice.is_playing() and self.queue[0] == url:
                self.queue.pop(0)
                self.current_song = url
                voice.play(audio,after=lambda e: asyncio.run_coroutine_threadsafe(self.skip(ctx,True), self.bot.loop))

    # Disconnect voice Channel
    @commands.command(case_insensitive=True)
    async def disconnect(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
            await ctx.send("Disconnect voice channel")

    #Stop
    @commands.command(case_insensitive=True)
    async def stop(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        self.current_song = None
        await ctx.send("Audio stop")
        
    # Pause
    @commands.command(case_insensitive=True)
    async def pause(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Audio pause")
        else:
            await ctx.send("Audio not playing")

    #Resume
    @commands.command(case_insensitive=True)
    async def resume(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Audio resume")
        else:
            await ctx.send("The audio is not paused")

    #Skip
    @commands.command(case_insensitive=True)
    async def skip(self,ctx,*args):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        self.current_song = None
        if len(self.queue) == 0:
            return
        time.sleep(1)
        try:
            url = self.queue[0]
        except:
            return
        if True in args:
            await self.play(ctx,url,True)
        else:
            await self.play(ctx,url)
    @commands.command(case_insensitive=True)
    async def clear(self,ctx):
        self.queue.clear()
        
    @commands.command(case_insensitive=True)
    async def songsinqueue(self,ctx):
        messagetosend = ""
        if len(self.queue) == 0:
            await ctx.send("Nothing in queue.")
        elif len(self.queue) <= 25:
            for i in range(len(self.queue)):
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    messagetosend = messagetosend+","+ydl.extract_info(self.current_song,download=False).get('title',None)
                messagetosend = messagetosend+","+self.queue[i]
                await ctx.send(messagetosend)
        elif len(self.queue) > 25:
            await ctx.send("Too many songs in queue to display.")
    @commands.command(case_insensitive=True)
    async def addplaylist(self,ctx,url: str):
        if 'playlist' in url or 'list' in url:
            try:
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                RunSkip = False
                if voice != None and voice.is_connected() and not voice.is_playing() and len(self.queue) == 0:
                    RunSkip = True
                links = Playlist(url).video_urls
                for i in range(len(links)):
                    if not (links[i] in self.queue):
                        self.queue.append(links[i])
                if RunSkip == True:
                    asyncio.run_coroutine_threadsafe(self.skip(ctx),self.bot.loop)
            except:
                await ctx.send("Error adding playlist to queue")
        else:
            await ctx.send("Link is not a playlist")
    async def searchhandler(self,ctx,msg_id,url):
        time.sleep(5)
        vote_msg = await ctx.fetch_message(msg_id)
        upemotes = discord.utils.get(vote_msg.reactions,emoji="👍")
        downemotes = discord.utils.get(vote_msg.reactions,emoji="👎")
        upcount = 0 or upemotes.count
        downcount = 0 or downemotes.count
        goodjob = False
        if upcount > downcount:
            goodjob = True
        if upcount == downcount:
            goodjob = True
        if goodjob == True:
            asyncio.run_coroutine_threadsafe(self.play(ctx,url),loop=self.bot.loop)
    @commands.command(case_insensitive=True)
    async def ytsearch(self,ctx,*args):
        query = ' '.join(args)
        ytdl = youtube_dl.YoutubeDL(self.ydl_opts)
        video = ytdl.extract_info(query, download = False)['entries'][0]
        url = video["webpage_url"]
        vote_msg = await ctx.send(f"Is this the right video? {url}")
        await vote_msg.add_reaction('👍')
        await vote_msg.add_reaction('👎')
        asyncio.run_coroutine_threadsafe(self.searchhandler(ctx,vote_msg.id,url),self.bot.loop)
    @commands.command(case_insensitive=True)
    @commands.is_owner()
    async def closebot(self,ctx):
        await self.clear(ctx)
        try:
            await self.stop(ctx)
        except:
            pass
        try:
            await self.disconnect(ctx)
        except:
            pass
        await self.bot.close()
    @commands.command(case_insensitive=True)
    async def currentsong(self,ctx):
        if self.current_song == None:
            ctx.send("No song playing.")
        else:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ctx.send(f"Currently playing: {ydl.extract_info(self.current_song,download=False).get('title',None)}")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
