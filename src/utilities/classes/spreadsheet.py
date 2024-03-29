from setup import auth
from utilities.classes.commands import CommandSheet
from utilities.classes.triggers import TriggerSheet


class Spreadsheet:
    __key: str
    empty: bool
    commands: CommandSheet
    triggers: TriggerSheet

    def __init__(self, key: str | None):
        if not key:
            raise TypeError("The spreadsheet key is invalid.")

        self.__key = key
        self.refresh()

    def refresh(self):
        """Update the commands and triggers by requesting the spreadsheet's info again."""
        ss = auth.client.open_by_key(self.__key)
        self.commands = CommandSheet(ss.worksheet("commands").get_all_records())
        self.triggers = TriggerSheet(ss.worksheet("triggers").get_all_records())
        self.empty = not self.commands and not self.triggers
