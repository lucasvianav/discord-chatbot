import random
from typing import Callable

from discord import File, Message

from utilities import utils


async def good_morning(msg: Message):
    await utils.react_message(msg, ["🌞", "💛"])
    response = await msg.reply(f"Bom dia flor do dia, {msg.author.mention}!")
    await utils.react_response(response, "🌻")


async def good_afternoon(msg: Message):
    await utils.react_message(msg, ["🌇", "🧡"])
    response = await msg.reply(f"Boa tarde flor da tarde, {msg.author.mention}!")
    await utils.react_response(response, "💐")


async def good_night(msg: Message):
    await utils.react_message(msg, ["🌑", "💜"])
    response = await msg.reply(f"Boa noite flor da noite, {msg.author.mention}!")
    await utils.react_response(response, "🌼")


async def hi(msg: Message):
    roles = [role.name for role in msg.author.roles]
    await utils.react_message(
        msg, "🦆" if "Bixos" in roles or "Convidado(a)" in roles else "💩"
    )

    if "Presidência" in roles:
        output = "olá prezado presidente da SA-SEL"
        img = "images/prezado-presidente.png"
    elif "Bixos" in roles or "Convidado(a)" in roles:
        output = "oi meu anjo"
        img = None
    else:
        output = "oi arrombado"
        img = "images/oi-arrombado.jpg"

    response = await msg.reply(
        f"{output}, {msg.author.mention}!",
        file=(File(img) if img else None),
    )
    await utils.react_response(response, "🤪")


async def sad(msg: Message):
    await utils.react_message(msg, "😢")
    response = await msg.channel.send(
        f"oh céus, oh deus, oh vida :c",
        file=File("images/estou-devastado.png"),
    )
    await utils.react_response(response, "😿")


async def laugh(msg: Message):
    await utils.react_message(msg, "😂")
    response = await msg.channel.send("hahaha")
    await utils.react_response(response, "😹")


async def arthur(msg: Message):
    await utils.react_message(msg, "🐾")
    response = await msg.channel.send(
        "feliz nAUtAU", file=File("images/todão-arthur.png")
    )
    await utils.react_response(response, "🐶")


async def F(msg: Message):
    await utils.react_message(msg, "🪑")
    response = await msg.channel.send(
        random.choice(("que descanse em paz", "my thoughts and prayers"))
    )
    await utils.react_response(response)


triggers: dict[str, Callable] = {
    "bom dia": good_morning,
    "boa tarde": good_afternoon,
    "boa noite": good_night,
    "oi": hi,
    "triste": sad,
    "estou triste": sad,
    ":c": sad,
    ":(": sad,
    "risos": laugh,
    "auau": arthur,
    "au au": arthur,
    "nautau": arthur,
    "arthur": arthur,
    "f": F,
}
