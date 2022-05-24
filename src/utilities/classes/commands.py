from collections import defaultdict
from typing import Any

import discord
from discord import Message
from discord.ext.commands.context import Context

from utilities import logger, utils


class SheetCommand:
    """Object for a Discord command as defined in a Google Sheet's spreadsheet."""

    category: str
    name: str
    aliases: list[str]
    response_text: str
    response_images: list[str]
    tts: bool
    reply: bool

    def __init__(
        self,
        category: str,
        name: str,
        aliases: list[str] | str,
        response_text: str,
        response_images: list[str] | str,
        tts: bool | str,
        reply: bool | str,
    ):
        aliases = aliases.split("\n") if type(aliases) is str else list(aliases)
        response_images = (
            response_images.split("\n")
            if type(response_images) is str
            else list(response_images)
        )
        tts = utils.parse_sheet_boolean(tts) if type(tts) is str else bool(tts)
        reply = utils.parse_sheet_boolean(reply) if type(reply) is str else bool(reply)

        self.category = category.strip()
        self.name = name.strip()
        self.aliases = [a.strip() for a in aliases if a]
        self.response_text = response_text.strip()
        self.response_images = [
            i.replace("\n", "").replace(" ", "") for i in response_images if i
        ]
        self.tts = tts
        self.reply = reply

        if not SheetCommand.validate_name(self.name):
            raise ValueError("Invalid command name: ", self.name)
        if self.aliases and not any([SheetCommand.validate_name(alias) for alias in self.aliases]):
            raise ValueError("Invalid aliases: ", self.aliases)

    def __str__(self) -> str:
        names = "|".join(self.get_names())
        return (
            f"```>[{names}]\n\nCategoria: '{self.category}'.\n\nUm comando "
            "da planilha, responde com algum texto ou imagem.\nPara mais "
            'detalhes, envie ">spreadsheet".```'
        )

    def get_content(self) -> tuple[dict[str, Any], list[str]]:
        """Return a dict with the command's content to be passed directly into a Discord's `send()` method."""
        kwargs = {"content": self.response_text, "tts": self.tts}

        images = utils.get_images(self.response_images)

        if images:
            kwargs["files"] = [discord.File(img) for img in images]

        return kwargs, images

    def get_names(self) -> list[str]:
        """Get the list of the command's name and all of it's aliases."""
        return [self.name] + self.aliases

    async def send(
        self, ctx: Message | Context, emoji: str | list[str] = utils.RESPONSE_EMOJI
    ) -> Message:
        """
        Fire the command, sending it's contents to a message's channel/context.
        Also react to the sent message with given emoji.

        Parameters
        ----------
        ctx (Message | Context): either a message or a context to sent the command's contents in (if message, in it's channel).
        emoji (str | list[str]): emoji to react to the sent message with.

        Returns
        -------
        Message: the commands message.
        """
        kwargs, images = self.get_content()

        response = await (
            ctx.reply(**kwargs)
            if self.reply
            else utils.get_sender_method(ctx)(**kwargs)
        )

        logger.info("The response was successfully sent.", 2)
        await utils.react_response(response, emoji)

        if images:
            utils.delete_images(images)

        return response

    @staticmethod
    def validate_name(name: str):
        """Is `name` valid as a Discord command name/alias?"""
        has_newline = "\n" in name
        starts_with_prefix = name.startswith(">")
        has_space = " " in name

        return not (has_newline or starts_with_prefix or has_space)


class CommandSheet:
    """Object for a Google Sheet's spreadsheet containing Discord command definitions."""

    commands: list[SheetCommand]

    def __init__(self, ss: list[dict[str, str]]):
        self.commands = [
            SheetCommand(**self.__parse_row(row)) for row in ss if row["COMMAND NAME"]
        ]

    def get_command(self, cmd: str) -> SheetCommand | None:
        """
        Get of a command with a given name/alias.

        Parameters
        ----------
        cmd (str): commands' identifier (name or alias).

        Returns
        -------
        SheetCommand | None: the command object, if found.
        """
        if not SheetCommand.validate_name(cmd):
            return None

        for command in self.commands:
            if cmd == command.name or cmd in command.aliases:
                return command

    def get_category_commands(self, category: str) -> list[SheetCommand]:
        """Get of a category's commands."""
        return [cmd for cmd in self.commands if cmd.category == category]

    def get_categories_commands(self) -> dict[str, list[SheetCommand]]:
        """Get a dict in which each key is a category and each value is a list of that category's commands."""
        categories = defaultdict(list)

        for cmd in self.commands:
            categories[cmd.category].append(cmd)

        return categories

    def __parse_row(self, row: dict[str, str]) -> dict[str, str]:
        return {
            "category": row["COMMAND CATEGORY"],
            "name": row["COMMAND NAME"],
            "aliases": row["COMMAND ALIASES"],
            "response_text": row["RESPONSE TEXT"],
            "response_images": row["RESPONSE IMAGES"],
            "tts": row["TTS"],
            "reply": row["REPLY"],
        }
