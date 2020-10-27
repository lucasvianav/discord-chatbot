# import discord
import os
import requests

async def reactToResponse(bot, response, emojiList = False):
    if not emojiList: emojiList = []

    emojiList.insert(0, '🤠')
    for emoji in emojiList:
        try:
            await response.add_reaction(emoji)
        except:
            print(f"   [**] There was an error while reacting {emoji} to the response.")
        else:
            print(f"   [**] The reaction {emoji} was successfully added to the response.")

async def reactToMessage(bot, message, emojiList: list):
    for emoji in emojiList:
        try:
            await message.add_reaction(emoji)
        except:
            print(f"   [**] There was an error while reacting {emoji} to the message.")
        else:
            print(f"   [**] The reaction {emoji} was successfully added.")

def getImage(img: str):
    if img.startswith('http'):
        try: r = requests.get(img)

        except:
            print('   [**] Therewas an error with the image link: ' + img)
            img = False

        else:
            with open('aux.png', 'wb') as f: f.write(r.content)
            r.close()

            img = 'aux.png'
            print('   [**] The image was successfully downloaded.')

    else:
        print('   [**] There is no image to attach.')
        img = False

    return img

# Generates cogs based on the sheet's commands
def refreshCogs(bot, cogSheet: list, hasLoaded=True):
    # Unloads and then removes all cogs
    for filename in os.listdir('./cogs'): 
        if filename.endswith('.py'):
            if hasLoaded: bot.unload_extension(f'cogs.{filename.replace(".py","")}')
            os.remove(f'./cogs/{filename}')

    i = 0
    while i < len(cogSheet):
        auxCog = cogSheet[i]["COMMAND CATEGORY"]

        cog = open(f'./cogs/{auxCog}.py', 'w')

        cog.write("import os\n\n")

        cog.write("import discord\n")
        cog.write("from discord.ext import commands\n")
        cog.write("from util import *\n\n")

        cog.write(f"class {auxCog.title()}(commands.Cog):\n")
        cog.write("    def __init__(self, bot):\n")
        cog.write("        self.bot = bot\n\n")

        while i < len(cogSheet) and cogSheet[i]["COMMAND CATEGORY"] == auxCog:
            element = dict(cogSheet[i])

            aliases = [f"'{e}'" for e in element["COMMAND ALIASES"].split('\n')] if element["COMMAND ALIASES"] != "" else False
            if aliases and (("'" + element["COMMAND NAME"] + "'") in aliases): aliases.remove("'" + element["COMMAND NAME"] + "'")

            if aliases:
                cog.write(f"    @commands.command(aliases=[{', '.join(aliases)}])\n")
            else: 
                cog.write(f"    @commands.command()\n")
            cog.write("    async def %s(self, ctx):\n" % element["COMMAND NAME"])
            cog.write("        print(\"\\n [*] '>%s' command called.\")\n\n" % element["COMMAND NAME"])
            cog.write("        await reactToMessage(self.bot, ctx.message, ['🍉'])\n\n")

            cog.write("        img = '%s'\n" % element["RESPONSE IMAGE"])
            cog.write("        txt = \"\"\"%s\"\"\"\n\n" % element["RESPONSE TEXT"].replace("\n","\\n").replace("'","\\'").replace('"','\\"'))

            cog.write("        img = getImage(img)\n\n")

            cog.write("        if img:\n")
            cog.write("            response = await ctx.send(content=txt, file=discord.File(img))\n")
            cog.write("            os.remove(img)\n\n")

            cog.write("        else: response = await ctx.send(content=txt)\n\n")

            cog.write("        print('   [**] The response was successfully sent.')\n\n")

            cog.write("        await reactToResponse(self.bot, response)\n\n")

            i += 1

        cog.write("def setup(bot): \n")
        cog.write(f"    bot.add_cog({auxCog}(bot))\n")

        cog.close()

    # Loads all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename.replace(".py","")}')

    return

# if __name__ == "__main__":
#     refreshCogs(cogSheet)