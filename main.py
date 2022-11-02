import discord
import os
import asyncio
from discord.ext import commands

TOKEN = None
with open(os.path.dirname(os.path.abspath(__file__))+"\\token.txt") as f:
    TOKEN = f.read().split("\n")[0]

# Start Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

asyncio.run(bot.load_extension('cogs.commands'))

@bot.command(case_insensitive=True)
@commands.is_owner()
async def restart(ctx):
    await bot.reload_extension('cogs.commands')

bot.run(TOKEN)
