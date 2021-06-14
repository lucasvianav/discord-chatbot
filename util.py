import os
import re
from functools import reduce
import requests
from bs4 import BeautifulSoup

# constants
WELCOME_CHANNEL = 'random' # channel in which to send welcome message for new members
MESSAGE_EMOJI = '🍉' # emoji that'll be mainly used to react to user messages
RESPONSE_EMOJI = ':zenith_logo:' # emoji that'll be used to react to all bot messages
FIXED_COGS = [ # all cogs that aren't from the google sheet
    'Reuniões', 'OnMemberJoin', 'Decisions',
    'Counters', 'Utilities', 'Birthday'
]
AVAILABLE_REACTIONS = [ # list of reactions that'll be used in poll-like commands
    '🤠', '🍉', '💘', '🏂',
    '🧨', '🎂', '💣', '🎷', '🛹'
]
VOCATIVES = [ # list of vocatives that'll be used on the welcome message for new members
    'anjo', 'consagrado', 'comparsa',
    'amigo', 'caro', 'cumpadi', 'bonito',
    'campeão', 'tributarista', 'chegado',
    'peregrino', 'camponês', 'patrão',
    'donatário', 'bacharel', 'iluminado',
    'democrata', 'parnasiano', 'vacinado',
    'querido', 'barbeiro', 'zé', 'filho'
]

async def reactToResponse(bot, response, emojiList = []):
    if not emojiList: emojiList = []

    emojiList.insert(0, RESPONSE_EMOJI)
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

# downloads the image from a link and returns it's path
def getImage(img: str):
    if img.startswith('http'):
        try: r = requests.get(img)

        except:
            print('   [**] There was an error with the image link: ' + img)
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

# Writes all commands from cogSheets to disk
def writeCogs(cogSheet: list, commands: list):
    i = 0
    while i < len(cogSheet):
        auxCog = (cogSheet[i]["COMMAND CATEGORY"]).replace(' ', '_')

        if not auxCog:
            i += 1
            continue

        cog = open(f'./cogs/{auxCog}.py', 'w')

        cog.write("import os\n\n")

        cog.write("import discord\n")
        cog.write("from discord.ext import commands\n")
        cog.write("from util import *\n\n")

        cog.write(f"class {auxCog.title()}(commands.Cog):\n")
        cog.write("    def __init__(self, bot):\n")
        cog.write("        self.bot = bot\n\n")

        while i < len(cogSheet) and cogSheet[i]["COMMAND CATEGORY"] == auxCog.replace('_', ' '):
            element = dict(cogSheet[i])

            isNameInvalid = (not element["COMMAND NAME"]) or bool(re.search('^\d', element["COMMAND NAME"])) or bool(re.search('[^a-zA-Z\dáàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', element["COMMAND NAME"]))

            if not (element["COMMAND NAME"] in commands or isNameInvalid):
                aliases = [f"'{e}'" for e in element["COMMAND ALIASES"].split('\n')] if element["COMMAND ALIASES"] != "" else None
                if aliases:
                    # makes sure that each alias is unique
                    aliases = reduce(lambda acc, cur: acc + ([cur] if cur not in acc else []), aliases, [])

                    if (("'" + element["COMMAND NAME"] + "'") in aliases): aliases.remove("'" + element["COMMAND NAME"] + "'")
                    if "''" in aliases: aliases.remove("''")
                    if "' '" in aliases: aliases.remove("' '")

                tts = 'True' if element['TTS'] == 'TRUE' else 'False'
                reply = True if element['REPLY'] == 'TRUE' else False

                if aliases: cog.write(f"    @commands.command(aliases=[{', '.join(aliases)}])\n")
                else: cog.write(f"    @commands.command()\n")

                cog.write("    async def %s(self, ctx):\n" % element["COMMAND NAME"])
                cog.write("        await ctx.trigger_typing()\n\n")

                cog.write("        print(\"\\n [*] '>%s' command called.\")\n\n" % element["COMMAND NAME"])
                cog.write("        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])\n\n")

                cog.write("        img = '%s'\n" % element["RESPONSE IMAGE"])
                cog.write("        txt = \"\"\"%s\"\"\"\n\n" % element["RESPONSE TEXT"].replace("\n","\\n").replace("'","\\'").replace('"','\\"'))

                cog.write("        img = getImage(img)\n\n")

                cog.write("        if img:\n")
                cog.write(f"            response = await ctx.{'send' if not reply else 'reply'}(content=txt, file=discord.File(img), tts={tts})\n")
                cog.write("            os.remove(img)\n\n")

                cog.write(f"        else: response = await ctx.{'send' if not reply else 'reply'}(content=txt, tts={tts})\n\n")

                cog.write("        print('   [**] The response was successfully sent.')\n\n")

                cog.write("        await reactToResponse(self.bot, response)\n\n")

                commands.append(element["COMMAND NAME"])
                if aliases: commands.append(aliases)

            i += 1

        cog.write("def setup(bot): \n")
        cog.write(f"    bot.add_cog({auxCog.title()}(bot))\n")

        cog.close()

# Generates cogs based on the sheet's commands
def refreshCogs(bot, cogSheet: list, hasLoaded=True):
    if not os.path.isdir('./cogs'): os.mkdir('./cogs')

    # Unloads and then removes all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename.replace('.py', '') not in FIXED_COGS:
            if hasLoaded: bot.unload_extension(f'cogs.{filename.replace(".py","")}')
            os.remove(f'./cogs/{filename}')

    # List of all bot commands
    commands = [c.name for c in bot.commands] + reduce(lambda acc, cur: acc + [s for s in cur], [c.aliases for c in bot.commands], [])

    writeCogs(cogSheet, commands)

    # Loads all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and (filename.replace('.py', '') not in FIXED_COGS or not hasLoaded):
            bot.load_extension(f'cogs.{filename.replace(".py","")}')

    return
