import pymongo
from discord.ext import commands
from discord.utils import get
from util import *
from config import MONGODB_ATLAS_URI

class Counters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Database
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = client['discord-bot']['discord-bot']
        self.counters = self.db.find_one({"description": "counters"})['counters']

    # example of a command that uses a counter that increses each time it is called
    @commands.command(brief='', help='', aliases=[])
    async def júlio(self, ctx):
        await ctx.trigger_typing()

        logger.info(f"`>júlio` command called.")

        await utils.react_message(ctx.message, [MESSAGE_EMOJI])

        # increments that counter and saves it to the db
        self.counters['júlio'] += 1
        self.db.find_one_and_update({"description": "counters"}, {"$set": {"counters": self.counters}})

        response = await ctx.send(f'**Júlio ||Calandrin||, você é incrível e nós te amamos!** O Júlio já foi apreciado `{self.counters["júlio"]}` vezes.')

        await utils.react_response(response, ['❤️'])

def setup(bot):
    bot.add_cog(Counters(bot))

