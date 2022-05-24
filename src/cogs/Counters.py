from discord.ext import commands

from setup.config import db
from utilities import logger, utils


class Counters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counters = (
            obj["counters"] if (obj := db.find_one({"description": "counters"})) else {}
        )

    def update_counters(self):
        db.find_one_and_update(
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
