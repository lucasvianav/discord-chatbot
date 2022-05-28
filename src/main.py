import os
import random
from datetime import timedelta
from re import search

import discord
from discord.ext import tasks
from discord.utils import get

from setup import config
from setup.config import bot, db, sheet
from utilities import logger, utils
from utilities.triggers import triggers


@bot.event
async def on_ready():
    logger.info("The bot is running.")

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=">help")
    )
    logger.info("The bot's status was successfully set.")

    periodic_refresh.start()
    logger.info("The periodic refresh task was successfully started.")


@bot.event
async def on_member_join(member):
    logger.info(f"{member.display_name} has joined the server.")

    roles = (
        obj["roles"]
        if (obj := db.find_one({"description": "onMemberJoinRoles"}))
        else []
    )
    roles = [role for r in roles if (role := utils.parse_role(r, member.guild))]

    if roles:
        await member.add_roles(roles if len(roles) > 1 else roles[0])

    channel = get(member.guild.text_channels, name=utils.WELCOME_CHANNEL)

    if channel:
        response = await channel.send(
            f"{member.mention} Seja bem vindo(a), meu {random.choice(utils.VOCATIVES)}!"
        )
        await utils.react_response(response)
        logger.info("The welcome message was successfully sent.")
    else:
        logger.error(
            "The welcome message was not successfully sent because no welcome channel exists."
        )


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.content == ">":
        return

    if (trigger := message.content.lower()) in triggers:
        await triggers[trigger](message)
        return
    elif message.content == ">help":
        await utils.react_message(message)
    elif message.content.startswith(">help "):  # check for custom help texts
        await utils.react_message(message)
        target = message.content[6:]

        if target == "help":
            response = await message.channel.send(
                "```>help [comando|categoria]\n"
                "\nMostra essa mensagem.\n\nPara listar os comandos da planilha, "
                "envie '>help spreadsheet' ou '>help planilha'.```"
            )
            return
        elif command := sheet.commands.get_command(target):
            response = await message.channel.send(str(command))
            await utils.react_response(response)
            return
        elif category := sheet.commands.get_category_commands(target):
            lines = (
                [
                    "Categoria que faz parte da planilha, seus comandos ",
                    "respondem com algum texto ou imagem.",
                    "\n\nComandos:\n",
                ]
                + [f" {cmd.name}\n" for cmd in category]
                + ['\nPara mais detalhes, envie ">spreadsheet".']
            )
            messages = utils.create_messages_from_list(lines)
            for msg in messages:
                response = await message.channel.send(f"```{msg}```")
                await utils.react_response(response)
            return
        elif target in ["spreadsheet", "planilha"]:
            categories = sheet.commands.get_categories_commands()

            lines = [
                "Comandos definidos na planilha, que respondem com algum ",
                "texto ou imagem.\n\n[COMANDOS]\n",
            ]
            for category, commands in categories.items():
                lines += [f"{category}:\n"] + [f" {cmd.name}\n" for cmd in commands]
            lines += ['\nPara editar os comandos, envie ">spreadsheet".']

            messages = utils.create_messages_from_list(lines)
            for msg in messages:
                response = await message.channel.send(f"```{msg}```")
                await utils.react_response(response)
            return
    elif message.content.startswith(">") and (  # look for command
        command := sheet.commands.get_command(message.content[1:])
    ):
        logger.info(f"Command: '{command.name}', by {message.author.display_name}.")
        await utils.react_message(message)
        await command.send(message)
        return
    elif not message.content.startswith(">") and (
        trigger := sheet.triggers.get_trigger(message.content)
    ):
        logger.info(
            f"Trigger: '{message.content.lower()}', by {message.author.display_name}."
        )
        await utils.react_message(message)
        await trigger.send(message)
        return

    await bot.process_commands(message)


@bot.command(
    aliases=["dev", "créditos"],
    brief="Desenvolvimento do bot e repositório no GitHub.",
)
async def credits(ctx):
    await ctx.trigger_typing()
    logger.info("`>credits` command called.")

    await utils.react_message(ctx.message, ["🤙", "🍉", "😁", "💜", "👋", "💻"])

    response = await ctx.reply(
        "Esse bot foi originalmente desenvolvido pelo Flip em um momento de "
        "tédio e hoje é mantido pela Diretoria de Tecnologia.\n"
        "Obrigado pelo interesse <3.\n"
        "Repositório no GitHub: https://github.com/sa-sel/discord-bot."
    )
    logger.info("The response was successfully sent.", 2)
    await utils.react_response(response)


@bot.command(brief="Atualiza os comandos a partir da planilha.")
async def refresh(ctx):
    await ctx.trigger_typing()
    logger.info("`>refresh` command called.")
    await utils.react_message(ctx.message, ["🔝", "👌", "🆗"])

    sheet.refresh()

    if not sheet.empty:
        logger.info("The commands and triggers were successfully updated.", 2)
        response = await ctx.send("Comandos e triggers foram atualizados com sucesso.")
        await utils.react_response(response)
    else:
        logger.info("There are no commands nor triggers registered.", 2)
        response = await ctx.send("Não há comandos nem triggers cadastrados.")
        await utils.react_response(response, "😢")


@bot.command(
    aliases=["clean"],
    brief="Limpa o chat,",
    help="Exclui todas os comandos e mensagens do bot que foram enviadas nos últimos 10 minutos --- exceto mensagem 'importantes', como abertura de projetos.",
)
async def clear(ctx, delta="10min"):
    await ctx.trigger_typing()
    logger.info(f"`>clear` command called on the {ctx.channel.name} channel.")
    await utils.react_message(ctx.message, "⚰")

    delta = timedelta(seconds=utils.parse_time(delta) or -1)
    timestamp = ctx.message.created_at - delta

    important_regexes = [
        r"`\[ABERTURA DE PROJETOS\]`\n\n",
        r"`\[PRESENÇA DE REUNIÃO\]`\n\n",
        r"`\[VOTAÇÃO\]`\n\n",
    ]

    def filter_function(message):
        not_pinned = not message.pinned
        is_me = message.author == bot.user
        is_important = (
            [
                bool(match)
                for match in [
                    search(regex, message.content) for regex in important_regexes
                ]
                if match
            ]
            + [False]
        )[0]

        # hasPrefix = search('^>\S.*$', m.content)
        did_i_react = get(message.reactions, me=True)

        return not_pinned and not is_important and (is_me or did_i_react)

    deleted = await ctx.channel.purge(after=timestamp, check=filter_function)

    response = await ctx.send(
        f"`{len(deleted)} mensagens foram excluídas.`", delete_after=20
    )
    await utils.react_response(response)


@bot.command(
    brief="Manda uma mensagem no canal escolhido.",
    help="""
        Sintaxe: >send "$MENSAGEM" @ "$CANAL"

        Esse comando vai enviar a $MENSAGEM no $CANAL, em que $CANAL pode ser tanto o nome do canal desejado quanto sua mention.

        Por exemplo, o comando a seguir vai enviar "Oi! Tudo bem?" no canal "random":
        >send "Oi! Tudo bem?" @ "random".

        OBS: Tanto a mensagem quanto o canal desejado devem estar entre aspas e deve haver exatamente um espaço entre cada bloco do comando (mensagem, @ e \
        canal). Caso você queira que sua mensagem contenha uma arroba, escreva dentro dela \\@.

        (esse comando foi feito especialmente para o Júlio <3)
    """,
)
async def send(ctx, *argv):
    await ctx.trigger_typing()

    logger.info("`>send` command called.")
    await utils.react_message(ctx.message, ["🆗", "📢"])

    argv = " ".join(argv).split(" @ ")
    response = ""

    # checks if arguments are valid
    if len(argv) != 2 or not search('[^"]', argv[0]) or not search('[^"]', argv[1]):
        response = 'Os argumentos passados são inválidos. Para mais informações, envie ">help send".'
    else:
        message = argv[0].replace('"', "").replace("\\@", "@")
        channel_ref = argv[1].replace('"', "").replace("\\@", "@")

        channel = get(ctx.guild.text_channels, name=channel_ref) or get(
            ctx.guild.text_channels, mention=channel_ref
        )

        if channel:
            perms_user = channel.permissions_for(ctx.author)
            perms_me = channel.permissions_for(ctx.guild.me)

            # checks permissions
            if not perms_me.send_messages or not perms_me.read_messages:
                response = (
                    "Infelizmente eu não tenho permissão para mandar/visualizar"
                    + f" mensagens no {channel.mention}... *O que será que eles"
                    + " têm a esconder, hein?!*"
                )

            # if all permissions are ok
            elif perms_user.send_messages and perms_user.read_messages:
                message = await channel.send(message)
                await utils.react_message(message, ["🤠", "📢"])
                response = f"A mensagem foi enviada com sucesso no {channel.mention}."

            else:
                response = f"Infelizmente você não tem permissão para mandar mensagens {channel.mention}"
        else:
            response = f"Infelizmente o canal `{channel_ref}` não foi encontrado."

    response = await ctx.reply(response)
    await utils.react_response(response)


@bot.command(
    aliases=["sheet", "planilha", "commands", "comandos"],
    brief="Mostra o link da planilha de comandos do bot.",
)
async def spreadsheet(ctx):
    await ctx.trigger_typing()

    logger.info("`>spreadsheet` command called.")
    await utils.react_message(ctx.message)

    response = await ctx.reply(
        "Segue o link para a planilha com os ~~comandos do bot~~ meus comandos. "
        f"Use-a com cuidado.\nhttps://docs.google.com/spreadsheets/d/{config.SPREADSHEET_KEY}"
    )
    await utils.react_response(response)


# Refreshes the sheets' commands and triggers every 15 minutes
@tasks.loop(minutes=15)
async def periodic_refresh():
    logger.info("Time for a periodic refresh.")
    sheet.refresh()
    end = " - none registered." if sheet.empty else "."
    logger.info("The commands and triggers were successfully updated" + end, 2)


if __name__ == "__main__":
    for filename in [f for f in os.listdir("./src/cogs") if f.endswith(".py")]:
        bot.load_extension(f'cogs.{filename.replace(".py","")}')
    bot.run(config.DISCORD_TOKEN)
