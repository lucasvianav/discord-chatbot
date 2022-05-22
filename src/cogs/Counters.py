import pymongo
from discord.ext import commands

import logger
import utils
from config import MONGODB_ATLAS_URI


class Counters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # database
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = client["discord-bot"]["discord-bot"]
        self.counters = (
            obj["counters"]
            if (obj := self.db.find_one({"description": "counters"}))
            else {}
        )

    def update_counters(self):
        self.db.find_one_and_update(
            {"description": "counters"}, {"$set": {"counters": self.counters}}
        )

    # example of a command that uses a counter that increses each time it is called
    @commands.command(brief="Uma demonstração de amor!", help="Testa aí.")
    async def júlio(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>júlio` command called.")

        await utils.react_message(ctx.message, [utils.MESSAGE_EMOJI])

        # increments that counter and saves it to the db
        self.counters["júlio"] += 1
        self.update_counters()

        response = await ctx.send(
            "**Júlio ||Calandrin||, você é incrível e nós te amamos!** O "
            + f"Júlio já foi apreciado `{self.counters['júlio']}` vezes."
        )

        await utils.react_response(response, "❤️")


def setup(bot):
    bot.add_cog(Counters(bot))
