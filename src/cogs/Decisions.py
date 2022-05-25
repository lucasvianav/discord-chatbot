import random
from asyncio import sleep
from random import shuffle

from discord.ext import commands

from utilities import logger, utils


class Decisions(commands.Cog):
    """Commands for decision-aiding-like functionalities, like chooshing an option from a list."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief='">d N" vai jogar um dado com N lados.',
        help='Vai jogar um dado com número de lados igual ao número passado. e.g. ">d 20" vai jogar um dado com 20 lados.',
    )
    async def d(self, ctx, number):
        """
        Roll a dice with a given number of sides.

        Parameters
        ----------
        number: int
            Number of sides for the dice.
        """
        await ctx.trigger_typing()

        number = abs(int(number))
        logger.info(f"`>d{number}` command called.")
        await utils.react_message(ctx.message, "❔")

        response = await ctx.reply(random.randint(1, number))
        await utils.react_response(response)

    @commands.command(aliases=["coinFLIP"], brief="Cara ou coroa?")
    async def coinflip(self, ctx):
        """Throw a coin."""
        await ctx.trigger_typing()
        logger.info("`>coinflip` command called.")
        await utils.react_message(ctx.message, "❔")

        response = await ctx.send(random.choice(["cara", "coroa"]))
        await utils.react_response(response, ["💸", "💰"])

    @commands.command(
        aliases=["escolher", "escolha"],
        brief="Escolhe um item de uma lista.",
        help='Escolhe um item aleatório dentre a lista passada (itens separados por " | ").\ne.g.: ">choose cara | coroa", ">choose pizza | hamburger | sushi"',
    )
    async def choose(self, ctx, *options):
        """
        Randomly choose one between a list of options.

        Parameters
        ----------
        options: list[str]
            List of options to choose from, each separated by `|`.
        """
        await ctx.trigger_typing()
        logger.info("`>choose` command called.")
        await utils.react_message(ctx.message, ["❔"])

        chosen = random.choice(utils.parse_piped_list(options))
        response = await ctx.reply(chosen)
        await utils.react_response(response, "❕")

    @commands.command(
        aliases=["votação", "votacao", "vote", "enquete"],
        brief="Auxilia na votação por emojis.",
        help=(
            "O bot vai enviar uma mensagem convidando as pessoas a adicionarem "
            "reações para votarem nas opções especificadas. Ele vai esperar 5 "
            "minutos (ou uma quantidade especificada por quem chamou o comando) "
            "e depois vai mandar uma mensagem com o resultado da votação.\n\n"
            "É possível fazer uma votação de no mínimo 2 e no máximo 9 itens por "
            'vez, separando-os por " | ".\ne.g.: ">poll estrogonofe | macarrão '
            'com calabresa"\n\nExiste também alguns parâmetros/argumentos '
            "opcionais que podem ser passados para o comando:\n * Se você quiser "
            'que eu marque algum cargo, basta adicionar o parâmetro "$mention=" '
            "seguido do nome do cargo a ser marcado;\n * Se quiser que a votação "
            'tenha um título, o parâmetro "$title=", seguido do título;\n * Se '
            'você quiser que a votação dure N minutos, adicione "$duration=N";\n '
            "* Se você quiser que eu também te forneça um relatório com quem "
            'votou em cada coisa, inclua "$report".\n\nO nome do cargo a ser '
            "marcado deve estar exatamente igual ao nome do cargo no Discord.\n"
            "Os parâmetros são opcionais e, se não forem fornecidos (ou se o cargo "
            "fornecido não for encontrado), a votação não terá título e nenhum "
            "cargo será marcado.\n\nPor exemplo:\n * Se você incluir "
            '"$mention=everyone", eu vou marcar @everyone ou "$mention=Moletons", '
            'eu vou marcar "@Moletons da Elétrica" ou "@Moletons", respectivamente;'
            '\n * Se você incluir "$title=Qual comida vocês preferem para o '
            'integra?" essa pergunta será usada como título da votação;\n '
            '* Se você incluir "$duration=10", o resultado da votação será '
            'apresentado 10 minutos após o seu inícios.\n\ne.g.: ">poll $title=Qual '
            "comida vocês preferem para o integra? | $mention=everyone | $duration=15min "
            '| $report | Estrogonofe | Macarrão com Calabresa", ">poll Estrogonofe | '
            "Macarrão com Calabresa | $title=Qual comida vocês preferem para o integra? "
            '| $report | $mention=everyone"\n\n'
            "Vale ressaltar que cada parâmetro pode ser fornecido apenas uma vez "
            'e o valor passado para "duration" deve ser um número.'
        ),
    )
    async def poll(self, ctx, *options):
        """
        Make a poll.

        Parameters
        ----------
        options: str
            List of options for the poll, each separated by `|`.
        """
        await ctx.trigger_typing()
        logger.info("`>poll` command called.")

        options = utils.parse_piped_list(options)

        target_settings = ["mention", "title", "report", "duration"]
        settings = utils.parse_settings_list(options, target_settings)

        # if errors
        if (
            len(options) > len(utils.AVAILABLE_REACTIONS)
            or len(options) <= 1
            or settings is None
        ):
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                ("Os parâmetros só podem ser definidos uma vez cada.")
                if settings is None
                else (
                    f"É possível votar entre 2 e {len(utils.AVAILABLE_REACTIONS)} opções ao mesmo tempo."
                )
                + "\nEnvie `>help poll` para mais informações."
            )
            await utils.react_response(response)

            return

        await utils.react_message(ctx.message, ["🆗"])

        if "duration" not in settings:
            settings["duration"] = "5min"

        mention = ""
        if "mention" in settings:
            if (settings["mention"]) != "str":
                await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

                response = await ctx.send(
                    'É necessário especificar um valor para o parâmetro "$mention".\nEnvie `>help poll` para mais informações.'
                )
                await utils.react_response(response)

                return

            mention = await utils.parse_role(settings["mention"], ctx.guild)

            # no role found
            if not mention:
                response = await ctx.send(
                    f"O cargo `{settings['mention']}` não existe."
                )
                await utils.react_response(response)
                return

            if settings["mention"].lower() != "everyone":
                mention = mention.mention

            mention = f"{mention} "

        available = utils.AVAILABLE_REACTIONS.copy()
        shuffle(available)

        settings["title"] = f"**{settings['title']}**" if "title" in settings else ""
        duration = utils.parse_time(settings["duration"])
        reactions = {options[i]: available[i] for i in range(len(options))}

        if not duration:
            response = await ctx.send("Essa duração é inválida.")
            await utils.react_response(response)
            return

        response = (
            f'`[VOTAÇÃO]`\n\n{mention}{settings["title"]}'
            + ("\n\n" if mention or settings["title"] else "")
            + "Reaja (nesta mensagem) com os respectivos emojis "
            + "para votar entre as opções a seguir.\n"
        )
        tmp = reactions.items()
        for opt, emoji in tmp:
            response += f"\n**{opt}**: {emoji}"
            reactions[emoji] = opt
        response += (
            f"\n\nDaqui a aproximadamente __{duration//60} minuto"
            f'{"s" if duration > 120 else ""}__, vou dar o resultado da enquete :)'
        )

        response = await ctx.send(response)
        await utils.react_message(response, list(reactions.values()))

        # Sleeps for the duration
        logger.info(
            f"This routine will sleep for {duration} seconds while it waits for users to react.",
            2,
        )
        await sleep(duration)
        logger.info("'>poll' command is done sleeping.")

        logger.info("Fetching message reactions.", 2)
        cached_msg = await ctx.fetch_message(response.id)
        logger.info(f"Fetched message's id: {cached_msg.id}", 2)

        # now add roles to users who reacted

        await ctx.trigger_typing()

        result = []
        server = ctx.guild

        for reaction in cached_msg.reactions:
            if reaction.emoji not in reactions.values():
                continue
            logger.info(f"Fetching who reacted {reaction.emoji}.", 2)

            people = await reaction.users().flatten()
            people = [
                await server.fetch_member(user.id).display_name
                for user in [member for member in people if not member.bot]
            ]

            result.append(
                {
                    "emoji": reaction.emoji,
                    "item": reactions[reaction.emoji],
                    "people": people,
                }
            )

        max_voters = max([len(item["people"]) for item in result])
        winners = [item for item in result if len(item["people"]) == max_voters]

        winner_reactions = [item["emoji"] for item in winners]
        winners = ", ".join(
            ["**" + item["item"] + "** (" + item["emoji"] + ")" for item in winners]
        )

        response = (
            f'`[VOTAÇÃO]`\n\n{mention}{settings["title"]}'
            + (
                f"\n(enquete convocada por {ctx.author.mention})"
                if settings["title"]
                else ""
            )
            + ("\n\n" if mention or settings["title"] else "")
            + f'__{"Opções vencedoras (empate)" if len(winner_reactions) > 1 else "Opção vencedora"}__: {winners}\n\n'
            + (
                f"\n(enquete convocada por {ctx.author.mention})"
                if settings["title"]
                else ""
            )
        )
        response = await ctx.send(response)
        await utils.react_message(response, winner_reactions)

        if "report" in settings:
            report = "\n\n".join(
                [
                    (
                        f'__Opção__: {item["item"]}\n'
                        f'__Reação__: {item["emoji"]}\n'
                        f'__Número de votos__: {len(item["people"])}\n'
                        f'__Votos__: {", ".join(item["people"]) if item["people"] else "-"}'
                    )
                    for item in result
                ]
            )

            response = await ctx.send(
                f"`[RELATÓRIO DA VOTAÇÃO]`\n\n{settings['title']}"
                + ("\n\n" if mention or settings["title"] else "")
                + "Respostas em ordem decrescente de número de votos:\n\n"
                + report
            )
            await utils.react_message(response, winner_reactions)


def setup(bot):
    bot.add_cog(Decisions(bot))
