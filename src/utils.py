import re

import discord
import requests
from discord.utils import get

import logger

# emoji that'll be mainly used to react to user messages
MESSAGE_EMOJI = "🍉"
# emoji that'll be used to react to all bot messages
RESPONSE_EMOJI = "🤠"

# TODO: un-hardcode this
# channel in which to send welcome message for new members
WELCOME_CHANNEL = "random"

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
    "miguel",
    "grande gatsby",
]


async def react_message(
    message: discord.Message, emoji: str | list[str] = MESSAGE_EMOJI
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
    response: discord.Message, emoji: str | list[str] = RESPONSE_EMOJI
) -> None:
    emojis = [emoji] if type(emoji) is str else emoji
    await react_message(response, emojis)


def get_images(links: list[str]) -> list[str]:
    """
    Download the images from the provided links to a temporary directory.

    Parameters
    ----------
        links (str[]): images' URLs

    Returns
    -------
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


def parse_time(time: str) -> int | None:
    """
    Parse a timestamp string to it's actual int value in seconds.

    Parameters
    ----------
    time: str
    The timestamp.

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
    items: list[str]
        List of items to be extracted from.
    target_settings: list[str]
        List of option names. Each will be preceded by '$'.

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
    role: str
    The role's name or mention.
    ctx: discord.ext.commands.Context
    The context in which to search for the role.

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
