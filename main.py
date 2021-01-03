import os

import discord
from discord.ext import commands, tasks

from config import *
from util import *

# Bot client
bot = commands.Bot(command_prefix='>')

def refreshBot():
    # Sets use of global variables
    global spreadsheet; global commandSheet; global triggerSheet

    spreadsheet, commandSheet, triggerSheet, isEmpty = refreshSheet()
    refreshCogs(bot, commandSheet)

    return isEmpty

# Load cog
@bot.command(aliases=['carregar', 'ativar'])
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")

    response = await ctx.send(f"A categoria de comandos '{extension}' foi carregada com sucesso.")
    await reactToResponse(bot, response)

    print(f"\n [*] The '{extension}' cog was successfully loaded.")

# Unload cog
@bot.command(aliases=['descarregar', 'desativar'])
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")

    response = await ctx.send(f"A categoria de comandos '{extension}' foi descarregada com sucesso.")
    await reactToResponse(bot, response)

    print(f"\n [*] The '{extension}' cog was successfully unloaded.")

# When the bot has finished loading after being launched
@bot.event
async def on_ready():
    print("\n [*] The bot is running.")

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=">help"))
    print("\n [*] The bot's status was successfully set.")

    periodicRefresh.start()
    print("\n [*] The periodic refresh task was successfully started.")

# Whenever a new message is sent to a channel the bot has access to
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if message.content.lower() == "bom dia":
        print(f"\n [*] Trigger: 'bom dia', by {message.author.display_name}.")

        # Reacts to the trigger message (definition in util.py)
        await reactToMessage(bot, message, ['🌞', '💛'])

        # Sends response message
        response = await message.channel.send(f"Bom dia flor do dia, {message.author.mention}!")
        await reactToResponse(bot, response, emojiList=['🌻']) # Reacts to the response message

        return

    # Checks for all triggers listed in the spreadsheet
    for element in triggerSheet:
        if message.content.lower() in element["TRIGGER"].split('\n'):
            print(f"\n [*] Trigger: '{message.content}', by {message.author.display_name}.")

            await reactToMessage(bot, message, ['🍉'])

            img = getImage(element["RESPONSE IMAGE"])

            # If an image link was specified
            if img: 
                response = await message.channel.send(content=element["RESPONSE TEXT"], file=discord.File(img))
                os.remove(img) # Deletes the image from local directory

            else:
                response = await message.channel.send(content=element["RESPONSE TEXT"])

            print("   [**] The response was successfully sent.")

            await reactToResponse(bot, response)

            return

    await bot.process_commands(message)

# Bot's developer
@bot.command(aliases=['créditos', 'creditos', 'dev'])
async def credits(ctx):
    print("\n [*] '>credits' command called.")

    await reactToMessage(bot, ctx.message, ['🤙', '🍉', '😁', '💜', '👋'])

    response = await ctx.send("Esse bot foi desenvolvido pelo Flip em um momento de tédio. Obrigado pelo interesse <3 \nGitHub: https://github.com/lucasvianav. \nRepositório no GitHub: https://github.com/lucasvianav/discord-chatbot.")
    print("   [**] The response was successfully sent.")
    await reactToResponse(bot, response)

# Calls refreshSheet() (definition in config.py)
@bot.command(aliases=['atualizar', 'update'])
async def refresh(ctx):
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

@bot.command()
async def ban(ctx, *user):
    print('\n [*] \'>ban\' command called.')

    await reactToMessage(bot, ctx.message, ['👺'])

    response = await ctx.send(f'O usuário \'' + ' '.join(user) + '\' foi banido.')

    await reactToResponse(bot, response, emojiList=['💀'])

# Refreshes the commands and triggers every half an hour
@tasks.loop(minutes=30)
async def periodicRefresh():
    print("\n [*] Time for a periodic refresh.")

    isEmpty = refreshBot()

    print("   [**] The commands and triggers were successfully updated", end="")
    print(" - none registered.") if isEmpty else print(".")


# MAIN
refreshCogs(bot, commandSheet, hasLoaded=False)
bot.run(DISCORD_TOKEN)
