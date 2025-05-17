import random
from asyncio import sleep

from discord import File
from discord.ext import commands

from utilities import logger, utils


class SuperMarselo(commands.Cog):
    """Crazy random commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Separa os times pro famigerado.",
        help=(
            "Esse comando separa dois times para jogar codenames, já "
            "selecionando quem vai ser o spymaster de cada time.\n\nÉ necessário estar conectado a um canal de voz com pelo "
            "menos mais três pessoas para ativar esse comando."
        ),
    )
    async def codenames(self, ctx):
        """Create a Codenames room."""
        await ctx.trigger_typing()
        logger.info("`>codenames` command called.")

        voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
        members = [m for m in voiceChannel.members if not m.bot] if voiceChannel else []

        if not voiceChannel or len(members) < 4:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "É necessário estar em um canal de voz para usar esse comando."
                if not voiceChannel
                else "É necessário no mínimo 4 pessoas para jogar Codenames."
            )
            await utils.react_response(response)

            return
        else:
            await utils.react_message(ctx.message, ["🎲", "🎮", "🏏", "🕹️"])

        logger.info(f"{len(members)} members are present.", 2)
        logger.info(f'A room will {"" if createRoom else "not"} be created.', 2)

        people = [member.mention for member in members]

        blueSpymaster = random.choice(people)
        people.remove(blueSpymaster)

        redSpymaster = random.choice(people)
        people.remove(redSpymaster)

        blueOperatives = []
        for _ in range(len(people) // 2):
            blueOperatives.append(random.choice(people))
            people.remove(blueOperatives[-1])

        redOperatives = people

        logger.info("The teams were created.", 2)

        response = await ctx.send(
            "`TÁ NA HORA DO CODENAMES GAROTADA`\n\n"
            + f"**Time azul**  🔵:\n__*Spymaster*__: {blueSpymaster}\n"
            + f'__*Operatives*__: {", ".join(blueOperatives)}\n\n**Time '
            + f"vermelho**  🔴:\n__*Spymaster*__: {redSpymaster}\n"
            + f'__*Operatives*__: {", ".join(redOperatives)}\n\n'
            + "Que vença o melhor time!"
        )
        await utils.react_response(response)

    @commands.command(brief="Press F to pay respects.")
    async def F(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>F` command called.")
        await utils.react_message(ctx.message, "⚰")
        response = await ctx.send("`Press F to Pay Respects`")
        await utils.react_response(response)

    @commands.command(brief="Chama um membro.", aliases=["cade", "kd"])
    async def cadê(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>cadê` command called.")
        await utils.react_message(ctx.message, ["🤬"])
        response = await ctx.send(
            f"**cadê vc otário??** {' '.join(user)}", file=File("images/cade-vc.png")
        )
        await utils.react_response(response, ["❔"])

    @commands.command(brief='"Bane" um "usuário" do servidor.')
    async def ban(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>ban` command called.")
        await utils.react_message(ctx.message, ["👺"])
        response = await ctx.send(f"O usuário '{' '.join(user)}' foi banido.")
        await utils.react_response(response, ["💀"])

    @commands.command(brief="Declara a saideira!")
    async def saideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>saideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            f"A saideira do {ctx.author.mention} está oficialmente declarada! "
            "A próxima partida será a última dele. Em caso de saideira de "
            'conversa, "a próxima partida" equivale aos próximos 30 minutos '
            "de um bom papo. \n\nPara mais informações, acione o comando "
            "`>regrasSaideira`."
        )
        await utils.react_response(response)

    @commands.command(
        brief="Regras relacionadas à saideira.",
        aliases=["regrassaideira", "regrasaideira"],
    )
    async def regrasSaideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>regrasSaideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            "**A REGRA É CLARA!**\n\nA saideira precisa ser previamente "
            "declarada com uso do comando `>saideira`. Caso contrário, a "
            "saideira é inválida e todos têm direito de acionar o comando "
            "`>kakashi` para quem descumpriu a regra.\n\nA partir do momento "
            "em que a saideira for declarada, o declarante deve continuar "
            "jogando por no mínimo mais uma (01) partida e, no máximo, duas "
            "(02) - depois desse tempo, a saideira expira e deverá ser "
            "declarada novamente. Vale lembrar, que a 'partida' da saideira de "
            "conversa equivale a 30 minutos de um bom papo."
        )
        await utils.react_response(response)


def setup(bot):
    bot.add_cog(SuperMarselo(bot))
