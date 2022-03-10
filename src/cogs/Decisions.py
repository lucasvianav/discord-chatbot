import random
from asyncio import sleep
from re import search

from discord.ext import commands
from discord.utils import get

import logger
import utils


class Decisions(commands.Cog):
    """
    Module for decision-aiding like commands, like chooshing an option from
    a list.
    """

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

    @commands.command(
        brief="Cara ou coroa?", aliases=["coinFLIP", "caracoroa", "caraoucoroa"]
    )
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
        help='Escolhe um item aleatório dentre a lista passada (itens separados por " | ").\ne.g.: ">choose cara | coroa", ">choose pizza | hamburger | sushi | acarajé"',
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
        await utils.react_response(response, emojiList="❕")

    @commands.command(
        aliases=["votação", "votar", "votacao", "vote", "enquete"],
        brief="Auxilia na votação por emojis.",
        help='O self.bot vai enviar uma mensagem convidando as pessoas a adicionarem reações para votarem nas opções especificadas. Ele vai esperar 5 minutos (ou uma quantidade especificada por quem chamou o comando) e depois vai mandar uma mensagem com o resultado da votação.\n\nÉ possível fazer uma votação de no mínimo 2 e no máximo 9 itens por vez, separando-os por " | ".\ne.g.: ">poll estrogonofe | macarrão com calabresa"\n\nExiste também alguns parâmetros/argumentos opcionais que podem ser passados para o comando:\n * Se você quiser que eu marque algum cargo, basta adicionar o parâmetro "$mention=" seguido do nome do cargo a ser marcado;\n * Se quiser que a votação tenha um título, o parâmetro "$title=", seguido do título;\n * Se você quiser que a votação dure N minutos, adicione "$duration=N";\n * Se você quiser que eu também te forneça um relatório com quem votou em cada coisa, inclua "$report".\n\nO nome do cargo a ser marcado deve estar exatamente igual ao nome do cargo no Discord.\nOs parâmetros são opcionais e, se não forem fornecidos (ou se o cargo fornecido não for encontrado), a votação não terá título e nenhum cargo será marcado.\n\nPor exemplo:\n * Se você incluir "$mention=everyone", eu vou marcar @everyone ou "$mention=Moletons", eu vou marcar "@Moletons da Elétrica" ou "@Moletons", respectivamente;\n * Se você incluir "$title=Qual comida vocês preferem para o integra?" essa pergunta será usada como título da votação;\n * Se você incluir "$duration=10", o resultado da votação será apresentado 10 minutos após o seu inícios.\n\ne.g.: ">poll $title=Qual comida vocês preferem para o integra? | $mention=everyone | $duration=15 | $report | Estrogonofe | Macarrão com Calabresa", ">poll Estrogonofe | Macarrão com Calabresa | $title=Qual comida vocês preferem para o integra? | $report | $mention=everyone"\n\nVale ressaltar que cada parâmetro pode ser fornecido apenas uma vez e o valor passado para "duration" deve ser um número.',
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
        options = [item for item in options if not item.isspace()]

        # parses formatting options
        remove_list = []
        invalid = False
        mention = None
        title = None
        duration = None
        report = False

        for i in range(len(options)):
            if options[i].startswith("$mention="):
                if mention:
                    invalid = True
                    break

                mention = options[i].replace("$mention=", "")
                remove_list.append(options[i])

            elif options[i].startswith("$title="):
                if title:
                    invalid = True
                    break

                title = options[i].replace("$title=", "")
                remove_list.append(options[i])

            elif options[i].startswith("$report"):
                if report:
                    invalid = True
                    break

                report = True
                remove_list.append(options[i])

            elif options[i].startswith("$duration="):
                if duration:
                    invalid = True
                    break

                # Sleep time in minutes
                try:
                    duration = abs(int(options[i].replace("$duration=", "")))
                except ValueError:
                    invalid = True
                    break

                remove_list.append(options[i])

        print(f"   [**] The passed items are: {', '.join(options)}.")

        if len(options) > len(AVAILABLE_REACTIONS) or len(options) <= 1 or invalid:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                (
                    'Os parâmetros "mention", "title" e "duration" só podem ser definidos uma vez cada. Além disso, o valor passado para "duration" deve ser um número.'
                )
                if invalid
                else (
                    f"É possível votar entre 2 e {len(AVAILABLE_REACTIONS)} opções ao mesmo tempo."
                )
                + "\nEnvie `>help poll` para mais informações."
            )
            await utils.react_response(response)

            return

        else:
            for item in remove_list:
                options.remove(item)

        await utils.react_message(ctx.message, ["🆗"])

        server = ctx.guild
        serverRoles = await server.fetch_roles()

        if not duration:
            duration = 5

        if mention:
            mentionText = mention
            mention = (
                server.default_role
                if mention.lower() == "everyone"
                else get(serverRoles, name=mention)
            )

            if not mention:
                response = await ctx.send(f"O cargo `{mentionText}` não existe.")
                await utils.react_response(response)
                return

            elif mentionText.lower() != "everyone":
                mention = mention.mention

        # Writes message
        reactions = {}
        response = f'`[VOTAÇÃO]`\n\n{mention if mention else ""}{" " if mention else ""}{"**" + title + "** " if title else ""}\n\nReaja (nesta mensagem) com os respectivos emojis para votar entre as opções a seguir.\n'
        for item in options:
            newReaction = random.choice(AVAILABLE_REACTIONS)
            while newReaction in reactions.values():
                newReaction = random.choice(AVAILABLE_REACTIONS)

            response += f"\n**{item}**: {newReaction}"
            reactions[item] = newReaction
            reactions[newReaction] = item
        response += f'\n\nDaqui a __{duration} minuto{"s" if duration > 1 else ""}__, vou dar o resultado da enquete :)'

        response = await ctx.send(response)

        await utils.react_message(response, reactions.values())

        # Sleeps for $duration minutes
        print(
            f"   [**] This routine will sleep for {duration} minutes while it waits for users to react."
        )
        await sleep(60 * duration)
        print("\n [*] The '>poll' command is done sleeping.")

        print(f"   [**] Fetching message reactions.")
        cached = await ctx.fetch_message(response.id)
        print(f"   [**] Fetched message's id: {cached.id}")

        # Adds roles to users who reacted
        await ctx.trigger_typing()

        result = []
        for reaction in cached.reactions:
            if not reaction.emoji in reactions.values():
                continue

            print(f"   [**] Fetching who reacted {reaction.emoji}.")
            reactors = [
                (await server.fetch_member(user.id)).display_name
                for user in filter(
                    lambda member: not member.bot, await reaction.users().flatten()
                )
            ]

            result.append(
                {
                    "emoji": reaction.emoji,
                    "item": reactions[reaction.emoji],
                    "reactors": reactors,
                }
            )

        result.sort(reverse=True, key=lambda item: len(item["reactors"]))
        winners = list(
            filter(
                lambda item: len(item["reactors"]) == len(result[0]["reactors"]), result
            )
        )
        winnerReactions = [item["emoji"] for item in winners]

        result = "\n\n".join(
            [
                f'__Opção__: {item["item"]}\n__Reação__: {item["emoji"]}\n__Número de votos__: {len(item["reactors"])}\n__Votos__: {", ".join(item["reactors"]) if item["reactors"] else "-"}'
                for item in result
            ]
        )
        winners = ", ".join(
            ["**" + item["item"] + "** (" + item["emoji"] + ")" for item in winners]
        )

        response = await ctx.send(
            f'`[RESULTADO DA VOTAÇÃO]`\n\n{mention if mention else ""}{" " if mention else ""}'
            + (
                f"**{title}**\n(enquete convocada por {ctx.author.mention})\n\n"
                if title
                else ""
            )
            + f'__{"Opções vencedoras (empate)" if len(winnerReactions) > 1 else "Opção vencedora"}__: {winners}\n\n{"(enquete convocada por " + ctx.author.mention + ")" if not title else ""}'
        )
        await utils.react_message(response, winnerReactions)

        if report:
            response = await ctx.send(
                f'`[RELATÓRIO DA VOTAÇÃO]`\n\n{("**" + title + "** ") if title else ""}Respostas em ordem decrescente de número de votos:\n\n{result}'
            )
            await utils.react_message(response, winnerReactions)


def setup(bot):
    bot.add_cog(Decisions(bot))
