import os
import re
from typing import Callable

import discord
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from discord import Message
from discord.ext.commands.context import Context
from discord.utils import get

from utilities import logger

# emoji that'll be mainly used to react to user messages
MESSAGE_EMOJI = "🍉"
# emoji that'll be used to react to all bot messages
RESPONSE_EMOJI = "🤠"

# TODO: un-hardcode this
# channel in which to send welcome message for new members
WELCOME_CHANNEL = "random"

# TODO: un-hardcode this
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
    "🥰",
]

# TODO: un-hardcode this
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
    "comum",
    "consagrado",
    "cumpadi",
    "democrata",
    "donatário",
    "filho",
    "grande gatsby",
    "iluminado",
    "joca",
    "miguel",
    "parnasiano",
    "patrão",
    "peregrino",
    "querido",
    "tributarista",
    "vacinado",
    "zé",
]


async def react_message(
    message: Message, emoji: str | list[str] = MESSAGE_EMOJI
) -> None:
    emojis = [emoji] if type(emoji) == "str" else emoji

    for em in emojis:
        try:
            await message.add_reaction(em)
        except Exception:
            logger.exception(f"Something happened while reacting {em}.", 2)
        else:
            logger.info(f"The reaction {em} was successfully added.", 2)


async def react_response(
    response: Message, emoji: str | list[str] = RESPONSE_EMOJI
) -> None:
    emojis = [emoji] if type(emoji) is str else emoji
    await react_message(response, emojis)


def get_images(links: list[str]) -> list[str]:
    """
    Download the images from the provided links to a temporary directory.

    Parameters
    ----------
    links (list[str]): images' URLs

    Returns
    -------
    list[str]: paths to downloaded images
    """
    links = [url for url in links if url.startswith("http")]
    images = []

    if not os.path.isdir("./images"):
        os.mkdir("./images")

    for i, url in enumerate(links):
        # maximum of 10 images
        if i >= 10:
            break

        try:
            r = requests.get(url)
        except requests.ConnectionError or requests.HTTPError or requests.Timeout or requests.TooManyRedirects:
            logger.exception(f"There was an error with the image link: {url}", 2)
        else:
            filename = f"./images/tmp-{i}.png"
            images.append(filename)

            with open(filename, "wb") as f:
                f.write(r.content)

            logger.info(f"The image {i} was successfully downloaded.", 2)
            r.close()

    return images


def delete_images(paths: list[str]) -> None:
    """
    Delete the images in the provided paths, assuming they are in the `images` directory.
    Also deletes the `images` directory if it's empty.

    Parameters
    ----------
    paths (list[str]): images' URLs

    Returns
    -------
    list[str]: paths to downloaded images
    """
    paths = [path for path in paths if path.startswith("./images/")]
    for img in paths:
        os.remove(img)
    if not os.listdir("./images"):
        os.removedirs("./images")


def parse_time(time: str) -> int | None:
    """
    Parse a timestamp string to it's actual int value in seconds.

    Parameters
    ----------
    time (str): the timestamp.

    Returns
    -------
    int: value in seconds.
    """
    duration = int(re.sub(r"\D", "", time))
    unit = re.sub(r"\d", "", time)

    if ("minutes").startswith(unit):
        duration *= 60
    elif ("hours").startswith(unit):
        duration *= 3600
    elif ("seconds").startswith(unit):
        pass
    else:
        duration = None

    return duration


def parse_piped_list(items: list[str] | tuple[str]) -> list[str]:
    """Join all strings from a list and splits it by pipes."""
    return [
        item.replace(" \\| ", " | ")
        for item in " ".join(items).split(" | ")
        if not item.isspace()
    ]


def parse_settings_list(
    items: list[str], target_settings: list[str]
) -> dict[str, str] | None:
    """
    Extract a list of $-preceded settings from a list of strings.

    Parameters
    ----------
    items (list[str]): list of items to be extracted from.
    target_settings (list[str]): list of option names. Each will be preceded by '$'.

    Returns
    -------
    dict[str, str] | None: values for each option or None if an option is duplicated
    """
    settings = {}
    found_indexes = set()
    target_settings = ["$" + opt for opt in target_settings]

    for i, item in enumerate(items):
        # settings can have the "$option=value" format
        after_split = item.split("=", 1)

        if item in items or after_split[0] in target_settings:
            key, value = after_split if len(after_split) == 2 else (item, True)

            if key in settings:
                return None

            settings[key] = value
            found_indexes.add(i)

    for i in found_indexes:
        items.pop(i)

    return settings


async def parse_role(role: str, server: discord.Guild) -> discord.Role | None:
    """
    Find role with specified name in specified context.

    Parameters
    ----------
    role (str): the role's name or mention.
    server (discord.Guild): the server in which to search for the role.

    Returns
    -------
    discord.Role: the actual role object, if found.
    """
    server_roles = await server.fetch_roles()
    return (
        server.default_role
        if role.lower() == "everyone"
        else (get(server_roles, name=role) or get(server_roles, mention=role))
    )


def in_diretoria(author: discord.Member) -> bool:
    """Determine if a member belongs to the directory."""
    return "Diretoria" in [role.name for role in author.roles]


def get_member_name(member) -> str:
    """Get the member's name and nickname."""
    return f"`{member.nick} ({member.name})`" if member.nick else f"`{member.name}`"


def create_messages_from_list(lines: list[str]) -> list[str]:
    """
    Create a list of Discord messages with less than 2000 characters from off of a list of lines.

    Parameters
    ----------
    lines (list[str]): list of strings to make up the messages.

    Returns
    -------
    list[str]: list of messages to be sent
    """
    messages: list[str] = []

    # clip messages to max 2000 characters (Discord limitation)
    while lines:
        text = ""
        while lines and len(text) + len(lines[0]) <= 1990:
            text += lines.pop(0)
        messages.append(text)

    return messages


def get_sender_method(ctx: Message | Context) -> Callable:
    """Return a function to send a Discord message to either a context or a message's channel."""
    if type(ctx) is Context:
        return ctx.send
    elif type(ctx) is Message:
        return ctx.channel.send

    # will never happen
    return lambda x: x


def parse_sheet_boolean(v: str):
    """Convert a Google Sheet's boolean (in form of string) to a Python bool."""
    return v == "TRUE"


def get_words() -> list[str]:
    """Get a list of words from a portuguese online dictionary's website."""
    r = requests.get("https://www.dicionarioinformal.com.br/")
    soup = BeautifulSoup(r.text, "html.parser")
    divs = soup.find("div", class_="col-sm-12 col-md-4")
    words = divs.findAll("span") if divs and type(divs) is Tag else []
    return [word.text for word in words]
