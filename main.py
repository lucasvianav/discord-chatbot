import os
import random
from datetime import timedelta
from re import search, sub

import discord
import pymongo
from discord.ext import commands, tasks
from discord.utils import get

from config import *
from util import *

# mongo database
client = pymongo.MongoClient(MONGODB_ATLAS_URI)
db = client['discord-bot']['discord-bot']

# Manage members permission
intents = discord.Intents.default()
intents.members = True

# Bot client
bot = commands.Bot(command_prefix='>', intents=intents)

# Refreshes the sheets' commands and triggers
def refreshBot():
    # Sets use of global variables
    global spreadsheet; global commandSheet; global triggerSheet

    spreadsheet, commandSheet, triggerSheet, isEmpty = refreshSheet()
    refreshCogs(bot, commandSheet)

    return isEmpty

# When the bot has finished loading after being launched
@bot.event
async def on_ready():
    print("\n [*] The bot is running.")

    # COMPREM MOLETONS
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=">moletons"))
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=">help"))
    print("\n [*] The bot's status was successfully set.")

    periodicRefresh.start()
    print("\n [*] The periodic refresh task was successfully started.")

# Whenever a member joins the server
@bot.event
async def on_member_join(member):
    print(f"\n [*] {member.display_name} has joined the server.")

    # Gets all roles that sould be added to the members
    roles = db.find_one({"description": "onMemberJoinRoles"})['roles']
    roles = list(filter(lambda r: r, map(lambda r: get(member.guild.roles, name=r), roles)))

    # If there are any roles to be added, add them to the member that just joined
    if roles: await member.add_roles(roles if len(roles) > 1 else roles[0])

    # Sends a welcome message at the WELCOME_CHANNEL
    channel = get(member.guild.text_channels, name=WELCOME_CHANNEL)
    response = await channel.send(f'{member.mention} Seja bem vindo(a), meu {random.choice(VOCATIVES)}!')
    print("   [**] The welcome message was successfully sent.")

    await reactToResponse(bot, response)

# Whenever a new message is sent to a channel the bot has access to
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if message.content.lower() == "bom dia":
        print(f"\n [*] Trigger: 'bom dia', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🌞', '💛'])

        # Sends response message
        response = await message.reply(f"Bom dia flor do dia, {message.author.mention}!")
        await reactToResponse(bot, response, emojiList=['🌻']) # Reacts to the response message

        return

    if message.content.lower() == 'boa noite':
        print(f"\n [*] Trigger: 'boa noite', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🌑', '💜'])

        # Sends response message
        response = await message.reply(f"Boa noite flor da noite, {message.author.mention}!")
        await reactToResponse(bot, response, emojiList=['🌼']) # Reacts to the response message

        return

    if message.content.lower() == 'boa tarde':
        print(f"\n [*] Trigger: 'boa tarde', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🌇', '🧡'])

        # Sends response message
        response = await message.reply(f"Boa tarde flor da tarde, {message.author.mention}!")
        await reactToResponse(bot, response, emojiList=['💐']) # Reacts to the response message

        return

    if message.content.lower() in ['oi', 'oi arrombado']:
        print(f"\n [*] Trigger: 'oi arrombado', by {message.author.display_name}.")

        roles = [ role.name for role in message.author.roles ]

        await reactToMessage(bot, message, ['🦆'] if 'Bixos' in roles or 'Convidado(a)' in roles else ['💩'])

        if 'Presidência' in roles:
            output = 'olá prezado presidente da SA-SEL'
            img = './images/prezado-presidente.png'

        elif 'Bixos' in roles or 'Convidado(a)' in roles:
            output = "oi meu anjo"
            img = None

        else:
            output = 'oi arrombado'
            img = './images/oi-arrombado.jpg'

        response = await message.reply(f"{output}, {message.author.mention}!", file=(discord.File(img) if img else img))

        await reactToResponse(bot, response, emojiList=['🤪']) # Reacts to the response message

        return

    if message.content.lower() in ['triste', 'tristeza', 'estou triste', ':c', ':(', 'estou devastado', 'estou devastado por dentro']:
        print(f"\n [*] Trigger: 'estou devastado por dentro', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['😢'])

        # Sends response message
        response = await message.channel.send(f"oh céus, oh deus, oh vida :c", file=discord.File('./images/estou-devastado.png'))
        await reactToResponse(bot, response, emojiList=['😿']) # Reacts to the response message

        return

    if message.content.lower() == 'risos':
        print(f"\n [*] Trigger: 'risos', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['😂'])

        # Sends response message
        response = await message.channel.send(f"hahaha")
        await reactToResponse(bot, response, emojiList=['😹']) # Reacts to the response message

        return

    if message.content.lower() in ['auau',  'au au', 'nautau', '>arthur']:
        print(f"\n [*] Trigger: 'auau', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🐾'])

        # Sends response message
        response = await message.channel.send(f"feliz nAUtAU", file=discord.File('./images/todão-arthur.png'))
        await reactToResponse(bot, response, emojiList=['🐶']) # Reacts to the response message

        return

    if message.content == 'F':
        print(f"\n [*] Trigger: 'F', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🪑'])

        # Sends response message
        response = await message.channel.send(random.choice(['que descanse em paz', 'my thoughts and prayers']))
        await reactToResponse(bot, response) # Reacts to the response message

        return

    # Checks for all triggers listed in the spreadsheet
    for element in triggerSheet:
        if message.content and message.content.lower() in [ trigger for trigger in element["TRIGGER"].split('\n') if trigger ]:
            print(f"\n [*] Trigger: '{message.content}', by {message.author.display_name}.")

            await reactToMessage(bot, message, [MESSAGE_EMOJI])

            image_links = element["RESPONSE IMAGE"].split('\n')

            # gets image attatchment
            images = getImages(image_links)

            # activates text-to-speech if specified
            tts = element['TTS'] == 'TRUE'

            # If an image link was specified
            if images:
                # COMPREM MOLETONS
                response = await message.channel.send(content=element["RESPONSE TEXT"] + '\n\n**COMPREM MOLETONS!!!!!111!!!!** ENVIE `>moletons`', files=[ discord.File(img) for img in images ], tts=tts)

                # Deletes the image from local directory
                for img in images: os.remove(img)

            else:
                # COMPREM MOLETONS
                response = await message.channel.send(content=element["RESPONSE TEXT"] + '\n\n**COMPREM MOLETONS!!!!!111!!!!** ENVIE `>moletons`', tts=tts)

            print("   [**] The response was successfully sent.")

            await reactToResponse(bot, response)

            return

    await bot.process_commands(message)

# Bot's developer
@bot.command(brief='Desenvolvedor do bot e repositório no GitHub.', aliases=['créditos', 'creditos', 'dev'])
async def credits(ctx):
    await ctx.trigger_typing()

    print("\n [*] '>credits' command called.")

    await reactToMessage(bot, ctx.message, ['🤙', '🍉', '😁', '💜', '👋'])

    response = await ctx.reply("Esse bot foi desenvolvido pelo Flip em um momento de tédio. Obrigado pelo interesse <3 \nGitHub: https://github.com/lucasvianav. \nRepositório no GitHub: https://github.com/sa-sel/discord-bot.")
    print("   [**] The response was successfully sent.")
    await reactToResponse(bot, response)

# Calls refreshSheet() (definition in config.py)
@bot.command(brief='Atualiza os comandos a partir da planilha.', aliases=['atualizar', 'update'])
async def refresh(ctx):
    await ctx.trigger_typing()

    print("\n [*] '>refresh' command called.")

    await reactToMessage(bot, ctx.message, ['🔝', '👌', '🆗'])

    isEmpty = refreshBot()

    if not isEmpty:
        print("   [**] The commands and triggers were successfully updated.")
        response = await ctx.send("Os comandos e triggers foram atualizados com sucesso.")
        print("   [**] The response was successfully sent.")
        await reactToResponse(bot, response)

    else:
        print("   [**] There are no commands nor triggers registered.")
        response = await ctx.send("Não há comandos nem triggers cadastrados.")
        print("   [**] The response was successfully sent.")
        await reactToResponse(bot, response, emojiList=['😢'])

@bot.command(brief='"Bane" um "usuário" do servidor.')
async def ban(ctx, *user):
    await ctx.trigger_typing()

    print('\n [*] \'>ban\' command called.')

    await reactToMessage(bot, ctx.message, ['👺'])

    response = await ctx.send(f'O usuário \'' + ' '.join(user) + '\' foi banido.')

    await reactToResponse(bot, response, emojiList=['💀'])

@bot.command(brief='Chama um membro. e.g. ">cadê @pessoa"', aliases=['cade', 'kd'])
async def cadê(ctx, *user):
    await ctx.trigger_typing()

    print('\n [*] \'>cadê\' command called.')

    await reactToMessage(bot, ctx.message, ['🤬'])

    user = ' '.join(user)
    response = await ctx.send(f'**cadê vc otário??** {user}', file=discord.File('./images/cade-vc.png'))

    await reactToResponse(bot, response, emojiList=['❔'])

@bot.command(brief='Press F to pay respects.')
async def F(ctx):
    await ctx.trigger_typing()

    print('\n [*] \'>F\' command called.')

    await reactToMessage(bot, ctx.message, ['⚰️'])

    response = await ctx.send('`Press F to Pay Respects`')

    await reactToResponse(bot, response)

@bot.command(brief='Uma linda homenagem a uma cachorra natalina.')
async def arthur(ctx):
    await ctx.trigger_typing()

    ctx.content = '>arthur'
    await on_message(ctx)

# deletes all messages sent by the bot or that triggered it
# (does not delete "important" messages, like from >trackPresence and >openProjects commands)
@bot.command(
    aliases=['clean', 'limpar'],
    brief='Limpa o chat,',
    help='Exclui todas os comandos e mensagens do bot que foram enviadas nos últimos 10 minutos.'
)
async def clear(ctx):
    await ctx.trigger_typing()

    print(f'\n [*] \'>clear\' command called on the {ctx.channel.name} channel.')

    await reactToMessage(bot, ctx.message, ['⚰️'])

    timestamp = ctx.message.created_at - timedelta(minutes=10)

    def filterFunction(m):
        notPinned = not m.pinned
        isMe = (m.author == bot.user)
        isImportant = search(r'`\[ABERTURA DE PROJETOS\]`\n\n', m.content) or search(r'`\[PRESENÇA DE REUNIÃO\]`\n\n', m.content) or search(r'`\[VOTAÇÃO\]`\n\n', m.content)
        # hasPrefix = search('^>\S.*$', m.content)
        didIReact = get(m.reactions, me=True)
        isHelp = m.content == '>help'

        return isHelp or (notPinned and not isImportant and (isMe or didIReact))

    deleted = await ctx.channel.purge(after=timestamp, check=filterFunction)

    response = await ctx.send(f'`{len(deleted)} mensagens foram excluídas.`', delete_after=20)

    await reactToResponse(bot, response)

# Sends a passed message to the specified channel
@bot.command(
    brief='Manda uma mensagem no canal escolhido.',
    help='Sintaxe: >send "$MENSAGEM" @ "$CANAL"\n\nEsse comando vai enviar a $MENSAGEM no $CANAL, em que $CANAL pode ser tanto o nome do canal desejado quanto sua mention.\n\nPor exemplo, o comando a seguir vai enviar "Oi! Tudo bem?" no canal "random":\n>send "Oi! Tudo bem?" @ "random".\n\nOBS: Tanto a mensagem quanto o canal desejado devem estar entre aspas e deve haver exatamente um espaço entre cada bloco do comando (mensagem, @ e canal). Caso você queira que sua mensagem contenha uma arroba, escreva dentro dela \\@.\n\n(esse comando foi feito especialmente para o Júlio <3)',
    aliases=[]
)
async def send(ctx, *argv):
    await ctx.trigger_typing()

    print('\n [*] \'>send\' command called.')
    await reactToMessage(bot, ctx.message, ['🆗', '📢'])

    argv = " ".join(argv)
    argv = argv.split(' @ ')

    # checks if arguments are valid
    if len(argv) != 2 or not search('[^"]', argv[0]) or not search('[^"]', argv[1]):
        response = 'Os argumentos passados são inválidos. Para mais informações, envie ">help send".'

    else:
        message = sub('^"(.+)"$', r'\g<1>', argv[0]).replace('\\@', '@')
        channelRef = sub('^"(.+)"$', r'\g<1>', argv[1]).replace('\\@', '@')

        channel = get(ctx.guild.text_channels, name=channelRef) or get(ctx.guild.text_channels, mention=channelRef)

        # if the channel exists
        if channel:
            permissionsUser= channel.permissions_for(ctx.author)
            permissionMe = channel.permissions_for(ctx.guild.me)

            # checks permissions
            if not permissionMe.send_messages or not permissionsUser.read_messages:
                response = f'Infelizmente eu não tenho permissão para mandar/visualizar mensagens no {channel.mention}... *O que será que eles têm a esconder, hein?!*'

            # if all permissions are ok
            elif permissionsUser.send_messages and permissionsUser.read_messages:
                message = await channel.send(message)
                await reactToMessage(bot, message, ['🤠', '📢'])

                response = f'A mensagem foi enviada com sucesso no {channel.mention}.'

            else:
                response = f'Infelizmente você não tem permissão para mandar mensagens {channel.mention}'

        # if the channel does not exist
        else:
            response = f'Infelizmente o canal passado (`{channelRef}`) não foi encontrado.'

    response = await ctx.reply(response)

    await reactToResponse(bot, response)

# Refreshes the sheets' commands and triggers every 15 minutes
@tasks.loop(minutes=15)
async def periodicRefresh():
    print("\n [*] Time for a periodic refresh.")

    isEmpty = refreshBot()

    print("   [**] The commands and triggers were successfully updated", end="")
    print(" - none registered.") if isEmpty else print(".")


if __name__ == '__main__':
    refreshCogs(bot, commandSheet, hasLoaded=False)
    bot.run(DISCORD_TOKEN)
