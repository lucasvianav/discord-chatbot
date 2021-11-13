import re

import discord
import requests

import logger

#  ____ ___  _   _ ____ _____  _    _   _ _____ ____
# / ___/ _ \| \ | / ___|_   _|/ \  | \ | |_   _/ ___|
# | |  | | | |  \| \___ \ | | / _ \ |  \| | | | \___ \
# | |__| |_| | |\  |___) || |/ ___ \| |\  | | |  ___) |
# \____\___/|_| \_|____/ |_/_/   \_\_| \_| |_| |____/

MESSAGE_EMOJI = "🍉"  # emoji that'll be mainly used to react to user messages
RESPONSE_EMOJI = "🤠"  # emoji that'll be used to react to all bot messages

# TODO: un-hardcode this
WELCOME_CHANNEL = "random"  # channel in which to send welcome message for new members

AVAILABLE_REACTIONS = [
    "🍉",
    "🎂",
    "🎷",
    "🏂",
    "👋",
    "💘",
    "💜",
    "💣",
    "💻",
    "😁",
    "🛹",
    "🤙",
    "🤠",
    "🧨",
]

# list of vocatives to be used on the
# welcome message for new members
VOCATIVES = [
    "amigo",
    "anjo",
    "bacharel",
    "barbeiro",
    "bonito",
    "campeão",
    "camponês",
    "caro",
    "chegado",
    "comparsa",
    "consagrado",
    "cumpadi",
    "democrata",
    "donatário",
    "filho",
    "iluminado",
    "parnasiano",
    "patrão",
    "peregrino",
    "querido",
    "tributarista",
    "vacinado",
    "zé",
    "comum",
    "joca",
]


# _____ _   _ _   _  ____ _____ ___ ___  _   _ ____
# |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___|
# | |_  | | | |  \| | |     | |  | | | | |  \| \___ \
# |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
# |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/


async def react_message(message: discord.Message, emojis: str or list[str]) -> None:
    if type(emojis) == "str":
        emojis = [emojis]

    for emoji in emojis:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException or discord.NotFound or discord.InvalidArgument:
            logger.exception(f"Something happened while reacting {emoji}.", 2)
        else:
            logger.info(f"The reaction {emoji} was successfully added.", 2)


async def react_response(response: discord.Message, emojis: str or list[str]) -> None:
    if type(emojis) == "str":
        emojis = [emojis]
    await react_message(response, [RESPONSE_EMOJI, *emojis])


def get_images(links: list[str]) -> list[str]:
    """
    Downloads the images from the provided links to a temporary directory.

    Parameters:
        links (str[]): images' URLs

    Returns:
        str[]: paths to downloaded images
    """

    links = [url for url in links if url.startswith("http")]
    images = []

    for i, url in enumerate(links):
        # maximum of 10 images
        if i >= 10:
            break

        try:
            r = requests.get(url)
        except requests.ConnectionError or requests.HTTPError or requests.Timout or requests.TooManyRedirects:
            logger.exception(f"There was an error with the image link: {url}", 2)
        else:
            filename = f"./images/tmp-{i}.png"
            images.append(filename)

            with open(filename, "wb") as f:
                f.write(r.content)

            logger.info(f"The image {i} was successfully downloaded.", 2)
        finally:
            r.close()

    return images


def parse_time(time: str) -> float or None:
    duration = int(re.sub(r"\D", "", time, "g"))
    unit = re.sub(r"\d", "", time, "g")

    if ("minutes").startswith(unit):
        duration *= 60
    elif ("hours").startswith(unit):
        duration *= 3600
    elif ("seconds").startswith(unit):
        pass
    else:
        duration = None

    return duration
