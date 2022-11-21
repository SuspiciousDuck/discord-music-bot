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
        self.queuey = []
        self.current_song = None
        self.loopy = False
        self.cmdnames = ["!connect","!disconnect","!play","!stop","!pause","!resume","!skip","!clear","!queue","!addplaylist","!ytsearch","!currentsong","!loop"]
        self.cmddescs = ["connect voice channel","disconnect voice channel","play audio","stop audio","pause audio","resume audio","skip audio","clear queue","sends the queue", "queue playlist","plays first result of query","sends audio name","loops playing song"]
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
        for i in range(len(self.cmdnames)):
            embed.add_field(name=self.cmdnames[i],value=self.cmddescs[i],inline=False)
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

        def loophandler(self,url):
            if self.loopy == False:
                asyncio.run_coroutine_threadsafe(self.skip(ctx,True), self.bot.loop)
            elif self.loopy == True:
                while True:
                    time.sleep(.25)
                    if voice.is_playing() == False:
                        break
                asyncio.run_coroutine_threadsafe(self.play(ctx,url),self.bot.loop)
        
        #check if bot is connected to voice channel
        if duration == None:
            await ctx.send("Couldn't retrieve duration data, try again or choose a different song.")
        if voice.is_connected() and duration != None:
            if not (True in args):
                self.queuey.append(url)
            if not voice.is_playing() and self.queuey[0] == url:
                self.queuey.pop(0)
                self.current_song = url
                voice.play(audio,after=lambda e: loophandler(self,url))
                await ctx.send(f"Now Playing: {youtube_dl.YoutubeDL(self.ydl_opts).extract_info(self.current_song,download=False).get('title',None)}")

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
        if len(self.queuey) == 0:
            return
        time.sleep(1)
        try:
            url = self.queuey[0]
        except:
            return
        if True in args:
            await self.play(ctx,url,True)
        else:
            await self.play(ctx,url)
    @commands.command(case_insensitive=True)
    async def clear(self,ctx):
        self.queuey.clear()
        
    @commands.command(case_insensitive=True)
    async def queue(self,ctx):
        messagetosend = ""
        if len(self.queuey) == 0:
            await ctx.send("Nothing in queue.")
        elif len(self.queuey) <= 25:
            for i in range(len(self.queuey)):
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    messagetosend = messagetosend+","+ydl.extract_info(self.current_song,download=False).get('title',None)
            await ctx.send(messagetosend)
        elif len(self.queuey) > 25:
            await ctx.send("Too many songs in queue to display.")
    @commands.command(case_insensitive=True)
    async def addplaylist(self,ctx,url: str):
        if 'playlist' in url or 'list' in url:
            try:
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                RunSkip = False
                if voice != None and voice.is_connected() and not voice.is_playing() and len(self.queuey) == 0:
                    RunSkip = True
                links = Playlist(url).video_urls
                for i in range(len(links)):
                    if not (links[i] in self.queuey):
                        self.queuey.append(links[i])
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
            await ctx.send("No song playing.")
        else:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                await ctx.send(f"Currently playing: {ydl.extract_info(self.current_song,download=False).get('title',None)}")
    @commands.command(case_insensitive=True)
    async def loop(self,ctx):
        scoob = self.loopy
        if scoob == True:
            self.loopy = False
        else:
            self.loopy = True
        await ctx.send(f"Looping: {self.loopy}")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
