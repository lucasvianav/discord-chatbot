import discord

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

def refreshCogs(commandSheet: list):
    for element in commandSheet:
        pass