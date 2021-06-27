import random
from asyncio import sleep
from re import search

from discord.ext import commands
from discord.utils import get

from config import *
from util import *


class Decisions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief='Também conhecido como "dois ou um".',
        help='Gera duas palavras ou números aleatórios para jogar "zerinho ou um" (aka "dois ou um").',
        aliases=['zeringo', 'zerinho', 'zerinhoum']
    )
    async def zerinho1(self, ctx):
        await ctx.trigger_typing()

        print('\n [*] \'>zerinho1\' command called.')

        await reactToMessage(self.bot, ctx.message, ['0️⃣', '❔', '1️⃣', '❓'])

        possibilities = ['número', 'palavra']
        output = [random.randint(0, 7777), random.randint(0, 7777)] if random.choice(possibilities) == 'número' else random.choices(getWords(), k=2)

        response = await ctx.send(f'-----------------------------\n`O ZERINHO OU UM OFICIAL É:`\n**{output[0]}** ou **{output[1]}**\n||boa sorte a todos||')

        await reactToResponse(self.bot, response)

    @commands.command(
        brief='">d N" vai jogar um dado com N lados.',
        help='Vai jogar um dado com número de lados igual ao número passado. e.g. ">d 20" vai jogar um dado com 20 lados.'
    )
    async def d(self, ctx, number):
        await ctx.trigger_typing()

        number = abs(int(number))

        print(f'\n [*] \'>d{number}\' command called.')

        await reactToMessage(self.bot, ctx.message, ['❔'])

        output = random.choice(['cara', 'coroa']) if number == 2 else random.randint(1, number)

        response = await ctx.reply(output)

        await reactToResponse(self.bot, response)

    @commands.command(brief='Cara ou coroa?', aliases=['coinFLIP', 'caracoroa', 'caraoucoroa'])
    async def coinflip(self, ctx):
        await ctx.trigger_typing()

        print('\n [*] \'>coinflip\' command called.')

        await reactToMessage(self.bot, ctx.message, ['❔'])

        output = random.choice(['cara', 'coroa'])

        response = await ctx.send(output)

        await reactToResponse(self.bot, response, emojiList=['💸', '💰'])

    @commands.command(
        aliases=['escolher', 'escolha'],
        brief='Escolhe um item de uma lista.',
        help='Escolhe um item aleatório dentre a lista passada (itens separados por " | ").\ne.g.: ">choose cara | coroa", ">choose pizza | hamburger | sushi | acarajé"'
    )
    async def choose(self, ctx, *options):
        await ctx.trigger_typing()

        print('\n [*] \'>choose\' command called.')
        await reactToMessage(self.bot, ctx.message, ['❔'])

        options = ' '.join(options).split(' | ')

        response = await ctx.reply(random.choice(options))

        await reactToResponse(self.bot, response, emojiList=['❕'])

    @commands.command(
        brief='Executa a milenar tática do chinelo.',
        help='Executa a clássica e milenar tática do chinelo para escolher entre duas opções, cunhada por Luís Corno. Você joga o chinelo e vê se ele cai de cabeça pra cima ou pra baixo - cada um é uma opção. Você pode, mas não precisa, selecionar duas opções passando-as separadas por | para o comando.\ne.g.: ">chinelo", ">chinelo pizza | hamburger"'
    )
    async def chinelo(self, ctx, *args):
        await ctx.trigger_typing()

        print('\n [*] \'>chinelo\' command called.')
        await reactToMessage(self.bot, ctx.message, ['👡', '🩰', '🥿', '🏑'])

        string = 'vou jogar o chinelo...'

        if args:
            args = ' '.join(args).split(' | ')

            if len(args) != 2:
                response = await ctx.reply('Você pode passar **nenhum** ou **dois** argumentos para esse comando, qualquer outra quantidade é inválida. Para mais informações, envie `>help chinelo`.')
                await reactToMessage(self.bot, response, ['🙅‍♂️', '❌', '🙅‍♀️'])
                return

            winner = { 'cima': args[0], 'baixo': args[1] }

            string += f'\n\nse cair virado pra cima, vai ser `{winner["cima"]}`. se cair virado pra baixo, vai ser `{winner["baixo"]}`.'

        response = await ctx.send(string, file=discord.File('./images/chinelo-1.jpg'))
        await reactToResponse(self.bot, response, emojiList=['1️⃣'])

        response = await ctx.send('estou jogando...', file=discord.File('./images/chinelo-2.jpg'))
        await reactToResponse(self.bot, response, emojiList=['2️⃣'])

        response = await ctx.send('joguei!!!', file=discord.File('./images/chinelo-3.jpg'))
        await reactToResponse(self.bot, response, emojiList=['3️⃣'])

        result = random.choices(['cima', 'baixo', 'lado'], weights=[3, 3, 1], k=1)[0]
        string = f'O CHINELO CAIU VIRADO **PR{("A " + result.upper()) if result != "lado" else "O LADO"}**!!!'
        if args: string += '\n\n' + (f'`{winner[result]}`' if result != 'lado' else 'infelizmente nenhuma opção') + ' venceu'

        response = await ctx.reply(string, file=discord.File(f'./images/chinelo-4-{result}.jpg'))
        await reactToResponse(self.bot, response, emojiList=['🧑‍💻'])

    @commands.command(
        aliases=['votação', 'votar', 'votacao', 'vote', 'enquete'],
        brief='Auxilia na votação por emojis.',
        help='O self.bot vai enviar uma mensagem convidando as pessoas a adicionarem reações para votarem nas opções especificadas. Ele vai esperar 5 minutos (ou uma quantidade especificada por quem chamou o comando) e depois vai mandar uma mensagem com o resultado da votação.\n\nÉ possível fazer uma votação de no mínimo 2 e no máximo 9 itens por vez, separando-os por " | ".\ne.g.: ">poll estrogonofe | macarrão com calabresa"\n\nExiste também alguns parâmetros/argumentos opcionais que podem ser passados para o comando:\n * Se você quiser que eu marque algum cargo, basta adicionar o parâmetro "$mention=" seguido do nome do cargo a ser marcado;\n * Se quiser que a votação tenha um título, o parâmetro "$title=", seguido do título;\n * Se você quiser que a votação dure N minutos, adicione "$duration=N";\n * Se você quiser que eu também te forneça um relatório com quem votou em cada coisa, inclua "$report".\n\nO nome do cargo a ser marcado deve estar exatamente igual ao nome do cargo no Discord.\nOs parâmetros são opcionais e, se não forem fornecidos (ou se o cargo fornecido não for encontrado), a votação não terá título e nenhum cargo será marcado.\n\nPor exemplo:\n * Se você incluir "$mention=everyone", eu vou marcar @everyone ou "$mention=Moletons", eu vou marcar "@Moletons da Elétrica" ou "@Moletons", respectivamente;\n * Se você incluir "$title=Qual comida vocês preferem para o integra?" essa pergunta será usada como título da votação;\n * Se você incluir "$duration=10", o resultado da votação será apresentado 10 minutos após o seu inícios.\n\ne.g.: ">poll $title=Qual comida vocês preferem para o integra? | $mention=everyone | $duration=15 | $report | Estrogonofe | Macarrão com Calabresa", ">poll Estrogonofe | Macarrão com Calabresa | $title=Qual comida vocês preferem para o integra? | $report | $mention=everyone"\n\nVale ressaltar que cada parâmetro pode ser fornecido apenas uma vez e o valor passado para "duration" deve ser um número.'
    )
    async def poll(self, ctx, *items):
        await ctx.trigger_typing()

        print('\n [*] \'>poll\' command called.')

        items = list(filter(lambda item: not search('^\s*$', item), ' '.join(items).split(' | ')))

        # parses formatting options
        removeList = []; invalid = False
        mention = None; title = None; duration = None; report = False
        for i in range(len(items)):
            if items[i].startswith('$mention='):
                if mention:
                    invalid = True
                    break

                mention = items[i].replace('$mention=', '')
                removeList.append(items[i])

            elif items[i].startswith('$title='):
                if title:
                    invalid = True
                    break

                title = items[i].replace('$title=', '')
                removeList.append(items[i])

            elif items[i].startswith('$report'):
                if report:
                    invalid = True
                    break

                report = True
                removeList.append(items[i])

            elif items[i].startswith('$duration='):
                if duration:
                    invalid = True
                    break

                # Sleep time in minutes
                try: duration = abs(int(items[i].replace('$duration=', '')))
                except ValueError:
                    invalid = True
                    break

                removeList.append(items[i])

        print(f"   [**] The passed items are: {', '.join(items)}.")

        if len(items) > len(AVAILABLE_REACTIONS) or len(items) <= 1 or invalid:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])

            response = await ctx.send(('Os parâmetros "mention", "title" e "duration" só podem ser definidos uma vez cada. Além disso, o valor passado para "duration" deve ser um número.') if invalid else (f'É possível votar entre 2 e {len(AVAILABLE_REACTIONS)} opções ao mesmo tempo.') + '\nEnvie `>help poll` para mais informações.')
            await reactToResponse(self.bot, response)

            return

        else:
            for item in removeList: items.remove(item)

        await reactToMessage(self.bot, ctx.message, ['🆗'])

        server = ctx.guild
        serverRoles = await server.fetch_roles()

        if not duration: duration = 5

        if mention:
            mentionText = mention
            mention = server.default_role if mention.lower() == 'everyone' else get(serverRoles, name=mention)

            if not mention:
                response = await ctx.send(f'O cargo `{mentionText}` não existe.')
                await reactToResponse(self.bot, response)
                return

            elif mentionText.lower() != 'everyone': mention = mention.mention

        # Writes message
        reactions = {}
        response = f'`[VOTAÇÃO]`\n\n{mention if mention else ""}{" " if mention else ""}{"**" + title + "** " if title else ""}\n\nReaja (nesta mensagem) com os respectivos emojis para votar entre as opções a seguir.\n'
        for item in items:
            newReaction = random.choice(AVAILABLE_REACTIONS)
            while newReaction in reactions.values(): newReaction = random.choice(AVAILABLE_REACTIONS)

            response += f'\n**{item}**: {newReaction}'
            reactions[item] = newReaction
            reactions[newReaction] = item
        response += f'\n\nDaqui a __{duration} minuto{"s" if duration > 1 else ""}__, vou dar o resultado da enquete :)'

        response = await ctx.send(response)

        await reactToMessage(self.bot, response, reactions.values())

        # Sleeps for $duration minutes
        print(f"   [**] This routine will sleep for {duration} minutes while it waits for users to react.")
        await sleep(60 * duration)
        print('\n [*] The \'>poll\' command is done sleeping.')

        print(f"   [**] Fetching message reactions.")
        cached = await ctx.fetch_message(response.id)
        print(f"   [**] Fetched message's id: {cached.id}")

        # Adds roles to users who reacted
        await ctx.trigger_typing()

        result = []
        for reaction in cached.reactions:
            if not reaction.emoji in reactions.values(): continue

            print(f"   [**] Fetching who reacted {reaction.emoji}.")
            reactors = [(await server.fetch_member(user.id)).display_name for user in filter(lambda member: not member.bot, await reaction.users().flatten())]

            result.append({
                "emoji": reaction.emoji,
                "item": reactions[reaction.emoji],
                "reactors": reactors
            })

        result.sort(reverse=True, key=lambda item: len(item["reactors"]))
        winners = list(filter(lambda item: len(item["reactors"]) == len(result[0]["reactors"]), result))
        winnerReactions = [item["emoji"] for item in winners]

        result = '\n\n'.join([f'__Opção__: {item["item"]}\n__Reação__: {item["emoji"]}\n__Número de votos__: {len(item["reactors"])}\n__Votos__: {", ".join(item["reactors"]) if item["reactors"] else "-"}' for item in result])
        winners = ", ".join(["**" + item["item"] + "** (" + item["emoji"] + ")" for item in winners])

        response = await ctx.send(f'`[RESULTADO DA VOTAÇÃO]`\n\n{mention if mention else ""}{" " if mention else ""}' + (f"**{title}**\n(enquete convocada por {ctx.author.mention})\n\n" if title else "") + f'__{"Opções vencedoras (empate)" if len(winnerReactions) > 1 else "Opção vencedora"}__: {winners}\n\n{"(enquete convocada por " + ctx.author.mention + ")" if not title else ""}')
        await reactToMessage(self.bot, response, winnerReactions)

        if report:
            response = await ctx.send(f'`[RELATÓRIO DA VOTAÇÃO]`\n\n{("**" + title + "** ") if title else ""}Respostas em ordem decrescente de número de votos:\n\n{result}')
            await reactToMessage(self.bot, response, winnerReactions)


def setup(bot):
    bot.add_cog(Decisions(bot))

