from discord.ext import commands

from setup.config import db
from utilities import logger, utils


class Counters(commands.Cog):
    """Commands that store and update a counter for how many times they were called."""

    def __init__(self, bot):
        self.bot = bot
        self.counters = (
            obj["counters"] if (obj := db.find_one({"description": "counters"})) else {}
        )

    def update_counters(self):
        """Update database."""
        db.find_one_and_update(
            {"description": "counters"}, {"$set": {"counters": self.counters}}
        )

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

    @commands.command(brief="Pra quando alguém nunca jogou algo.", help="Testa aí.")
    async def zani(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>zani` command called.")

        await utils.react_message(ctx.message, [utils.MESSAGE_EMOJI])

        # increments that counter and saves it to the db
        self.counters["zani"] += 1
        self.update_counters()

        response = await ctx.send(
            "**Ô Zani, explica aí como que joga, por favor!** O "
            f'Zani já explicou o jogo `{self.counters["zani"]}` vezes.'
        )
        await utils.react_response(response, "🎮")

    @commands.command(brief="Queria uma comida.", help="Testa aí.")
    async def fome(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>fome` command called.")

        await utils.react_message(ctx.message, [utils.MESSAGE_EMOJI])

        # increments that counter and saves it to the db
        self.counters["fome"] += 1
        self.update_counters()

        response = await ctx.send(
            "**TAÍS! O Flip pediu pra te perguntar, o que é que a gente vai "
            "comer????** O Flip e a Taís já ficaram indecisos sobre o que "
            f'jantar `{self.counters["fome"]}` vezes.'
        )
        await utils.react_response(response, ["🍲", "🥫"])


def setup(bot):
    bot.add_cog(Counters(bot))
