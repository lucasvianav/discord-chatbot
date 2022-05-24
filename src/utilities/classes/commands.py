from collections import defaultdict

from utilities import utils
from utilities.classes.discord import SheetDiscordInteraction


class SheetCommand(SheetDiscordInteraction):
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
        self.aliases = [a for e in aliases if (a := e.strip())]
        self.response_text = response_text.strip()
        self.response_images = [
            i for e in response_images if (i := e.replace("\n", "").replace(" ", ""))
        ]
        self.tts = tts
        self.reply = reply

        if not SheetCommand.validate_name(self.name):
            raise ValueError("Invalid command name: ", self.name)
        if self.aliases and not any(
            [SheetCommand.validate_name(alias) for alias in self.aliases]
        ):
            raise ValueError("Invalid aliases: ", self.aliases)

    def __str__(self) -> str:
        names = "|".join(self.get_names())
        return (
            f"```>[{names}]\n\nCategoria: '{self.category}'.\n\nUm comando "
            "da planilha, responde com algum texto ou imagem.\nPara mais "
            'detalhes, envie ">spreadsheet".```'
        )

    def get_names(self) -> list[str]:
        """Get the list of the command's name and all of it's aliases."""
        return [self.name] + self.aliases

    @staticmethod
    def validate_name(name: str):
        """Is `name` valid as a Discord command name/alias?"""
        has_newline = "\n" in name
        starts_with_prefix = name.startswith(">")
        has_space = " " in name

        return name and not (has_newline or starts_with_prefix or has_space)


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
