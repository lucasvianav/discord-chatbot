import os

import discord
import requests
from discord.ext import commands

from config import *
from util import *

# Bot client
bot = commands.Bot(command_prefix='>')

# When the bot has finished loading after being launched
@bot.event
async def on_ready():
    print(" [*] The bot is running.")

# Whenever a new message is sent to a channel the bot has access to
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if message.content.lower() == "bom dia saselers":
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

            # If an image link was specified
            if element["RESPONSE IMAGE"].startswith("http"):
                try: # Gets image from link
                    r = requests.get(element["RESPONSE IMAGE"]) 

                except: # If the link is broken
                    print("   [**] There was an error with the image link: " + element["RESPONSE IMAGE"])
                    img = False

                else: # If the link is fine
                    # Downloads the image and closes the website
                    with open("aux.png", "wb") as f: f.write(r.content)
                    r.close()

                    img = 'aux.png'
                    print("   [**] The image was successfully downloaded.")

            else: 
                print("   [**] There is no image to attach.")
                img = False

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

    response = await ctx.send("Esse bot foi desenvolvido pelo Flip em um momento de tédio. \nGitHub: https://github.com/lucasvianav. \nRepositório no GitHub: https://github.com/lucasvianav/discord-bot-sasel.")
    print("   [**] The response was successfully sent.")
    await reactToResponse(bot, response)

# Call refreshSheet()
@bot.command(aliases=['atualizar', 'update'])
async def refresh(ctx):
    print("\n [*] '>refresh' command called.")

    await reactToMessage(bot, ctx.message, ['🔝', '👌', '🆗'])

    response = refreshSheet()

    if response:
        print("   [**] The commands and triggers were successfully updated.")
        response = await ctx.send("Os comandos e triggers foram atualizados com sucesso.")
        print("   [**] The response was successfully sent.")
        await reactToResponse(bot, response)

    else:
        print("   [**] There are no commands nor triggers registered.")
        response = await ctx.send("Não há comandos nem triggers cadastrados.")
        print("   [**] The response was successfully sent.")
        await reactToResponse(bot, response, emojiList=['😢'])

bot.run(DISCORD_TOKEN)
