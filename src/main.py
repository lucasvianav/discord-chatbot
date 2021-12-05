import os
import random
from datetime import timedelta
from re import search

import discord
import pymongo
from discord.ext import commands, tasks
from discord.utils import get

import config
import logger
import utils

# mongo database
client = pymongo.MongoClient(config.MONGODB_ATLAS_URI)
db = client["discord-bot"]["discord-bot"]

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=">", intents=intents)


def __refresh_bot():
    """Refresh the sheets' commands and triggers."""
    (
        config.spreadsheet,
        config.command_sheet,
        config.trigger_sheet,
        isEmpty,
    ) = config.refresh_sheet()

    return isEmpty


@bot.event
async def on_ready():
    logger.info("The bot is running.")

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=">help")
    )
    logger.info("The bot's status was successfully set.")

    periodic_refresh.start()
    print("The periodic refresh task was successfully started.")


@bot.event
async def on_member_join(member):
    logger.info(f"{member.display_name} has joined the server.")

    roles = db.find_one({"description": "onMemberJoinRoles"})["roles"]
    roles = [role for role in [get(member.guild.roles, name=r) for r in roles] if role]

    if roles:
        await member.add_roles(roles if len(roles) > 1 else roles[0])

    channel = get(member.guild.text_channels, name=utils.WELCOME_CHANNEL)
    response = await channel.send(
        f"{member.mention} Seja bem vindo(a), meu {random.choice(utils.VOCATIVES)}!"
    )
    logger.info("The welcome message was successfully sent.")
    await utils.react_response(response)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # checks for all triggers listed in the spreadsheet
    for element in config.trigger_sheet:
        triggers = [trigger for trigger in element["TRIGGER"].split("\n") if trigger]

        if message.content and message.content.lower() in triggers:
            logger.info(
                f"Trigger: '{message.content}', by {message.author.display_name}."
            )
            await utils.react_message(message, [utils.MESSAGE_EMOJI])

            text = element["RESPONSE TEXT"]
            images = utils.get_images(element["RESPONSE IMAGE"].split("\n"))
            tts = element["TTS"] == "TRUE"

            if images:
                response = await message.channel.send(
                    content=text,
                    files=[discord.File(img) for img in images],
                    tts=tts,
                )

                for img in images:
                    os.remove(img)
            else:
                response = await message.channel.send(content=text, tts=tts)

            logger.info("The response was successfully sent.")
            await utils.react_response(response)

            return

    await bot.process_commands(message)


@bot.command(
    brief="Desenvolvedor do bot e repositório no GitHub.",
    aliases=["dev"],
)
async def credits(ctx):
    await ctx.trigger_typing()
    logger.info("`>credits` command called.")

    await utils.react_message(ctx.message, ["🤙", "🍉", "😁", "💜", "👋", "💻"])

    response = await ctx.reply(
        """Esse bot foi desenvolvido pelo Flip em um momento de tédio. Obrigado pelo interesse <3
        GitHub: https://github.com/lucasvianav.
        Repositório no GitHub: https://github.com/lucasvianav/discord-chatbot."""
    )
    logger.info("The response was successfully sent.", 2)
    await utils.react_response(response)


@bot.command(brief="Atualiza os comandos a partir da planilha.")
async def refresh(ctx):
    await ctx.trigger_typing()
    logger.info("`>refresh` command called.")

    await utils.react_message(ctx.message, ["🔝", "👌", "🆗"])

    isEmpty = __refresh_bot()

    if not isEmpty:
        logger.info("The commands and triggers were successfully updated.", 2)
        resp = await ctx.send("Os comandos e triggers foram atualizados com sucesso.")
        await utils.react_response(resp)
    else:
        logger.info("There are no commands nor triggers registered.", 2)
        resp = await ctx.send("Não há comandos nem triggers cadastrados.")
        await utils.react_response(resp, "😢")


@bot.command(
    aliases=["clean"],
    brief="Limpa o chat,",
    help="Exclui todas os comandos e mensagens do bot que foram enviadas nos últimos 10 minutos --- exceto mensagem 'importantes', como abertura de projetos.",
)
async def clear(ctx, delta: str = "10min"):
    await ctx.trigger_typing()
    logger.info(f"`>clear` command called on the {ctx.channel.name} channel.")

    await utils.react_message(ctx.message, "⚰️")

    delta = timedelta(seconds=utils.parse_time(delta))
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
                match
                for match in [
                    search(regex, message.content) for regex in important_regexes
                ]
                if match
            ]
            + [False]
        )[0]

        # hasPrefix = search('^>\S.*$', m.content)
        did_i_react = get(message.reactions, me=True)
        is_help = message.content == ">help"

        return is_help or (not_pinned and not is_important and (is_me or did_i_react))

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
    resp = ""

    # checks if arguments are valid
    if len(argv) != 2 or not search('[^"]', argv[0]) or not search('[^"]', argv[1]):
        resp = 'Os argumentos passados são inválidos. Para mais informações, envie ">help send".'
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
                resp = (
                    "Infelizmente eu não tenho permissão para mandar/visualizar"
                    + f" mensagens no {channel.mention}... *O que será que eles"
                    + " têm a esconder, hein?!*"
                )

            # if all permissions are ok
            elif perms_user.send_messages and perms_user.read_messages:
                message = await channel.send(message)
                await utils.react_message(message, ["🤠", "📢"])
                resp = f"A mensagem foi enviada com sucesso no {channel.mention}."

            else:
                resp = f"Infelizmente você não tem permissão para mandar mensagens {channel.mention}"
        else:
            resp = f"Infelizmente o canal `{channel_ref}` não foi encontrado."

    resp = await ctx.reply(resp)
    await utils.react_response(resp)


# Refreshes the sheets' commands and triggers every 15 minutes
@tasks.loop(minutes=15)
async def periodic_refresh():
    logger.info("Time for a periodic refresh.")
    end = " - none registered." if __refresh_bot() else "."
    logger.info("The commands and triggers were successfully updated" + end, 2)


if __name__ == "__main__":
    for filename in os.listdir("./cogs"):  # loads all cogs
        bot.load_extension(f'cogs.{filename.replace(".py","")}')
    bot.run(config.DISCORD_TOKEN)
