import os

import discord
from discord.ext import commands
from util import *

class Template(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=[''])
    async def comm(self, ctx):
        # stuff
        pass

def setup(bot):
    bot.add_cog(Template(bot))