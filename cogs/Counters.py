import pymongo
from discord.ext import commands

from config import MONGODB_ATLAS_URI
from util import *


class Counters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Database
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = client['discord-bot']['discord-bot']
        self.counters = self.db.find_one({"description": "counters"})['counters']

    @commands.command(brief='', help='', aliases=[])
    async def júlio(self, ctx):
        await ctx.trigger_typing()

        print(f'\n [*] \'>júlio\' command called.')

        await reactToMessage(self.bot, ctx.message, ['🍉'])

        # increments that counter and saves it to the db
        self.counters['júlio'] += 1
        self.db.find_one_and_update({"description": "counters"}, {"$set": {"counters": self.counters}})

        response = await ctx.send(f'**Júlio ||Calandrin||, você é incrível e nós te amamos!** O Júlio já foi apreciado `{self.counters["júlio"]}` vezes.' + (f'\n\nUau, {self.counters["júlio"]}... Que lindo marco, {ctx.author.mention}.' if not (self.counters["júlio"] % 1000) else ''))

        await reactToResponse(self.bot, response, ['❤️'])

    @commands.command(brief='', help='', aliases=[])
    async def zani(self, ctx):
        await ctx.trigger_typing()

        print(f'\n [*] \'>zani\' command called.')

        await reactToMessage(self.bot, ctx.message, ['🍉'])

        # increments that counter and saves it to the db
        self.counters['zani'] += 1
        self.db.find_one_and_update({"description": "counters"}, {"$set": {"counters": self.counters}})

        response = await ctx.send(f'**Ô Zani, explica aí como que joga, por favor!** O Zani já explicou o jogo `{self.counters["zani"]}` vezes.')

        await reactToResponse(self.bot, response, ['🎮'])

    @commands.command(brief='', help='', aliases=[])
    async def fome(self, ctx):
        await ctx.trigger_typing()

        print(f'\n [*] \'>fome\' command called.')

        await reactToMessage(self.bot, ctx.message, ['🍉'])

        # increments that counter and saves it to the db
        self.counters['fome'] += 1
        self.db.find_one_and_update({"description": "counters"}, {"$set": {"counters": self.counters}})

        response = await ctx.send(f'**TAÍS! O Flip pediu pra te perguntar, o que é que a gente vai comer????** O Flip e a Taís já ficaram indecisos sobre o que jantar `{self.counters["fome"]}` vezes.')

        await reactToResponse(self.bot, response, ['🍲', '🥫'])


def setup(bot):
    bot.add_cog(Counters(bot))

