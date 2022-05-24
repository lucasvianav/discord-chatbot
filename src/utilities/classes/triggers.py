from utilities import utils
from utilities.classes.discord import SheetDiscordInteraction


class SheetTrigger(SheetDiscordInteraction):
    """Object for a Discord trigger as defined in a Google Sheet's spreadsheet."""

    triggers: list[str]

    def __init__(
        self,
        triggers: list[str] | str,
        response_text: str,
        response_images: list[str] | str,
        tts: bool | str,
        reply: bool | str,
    ):
        triggers = triggers.split("\n") if type(triggers) is str else list(triggers)
        response_images = (
            response_images.split("\n")
            if type(response_images) is str
            else list(response_images)
        )
        tts = utils.parse_sheet_boolean(tts) if type(tts) is str else bool(tts)
        reply = utils.parse_sheet_boolean(reply) if type(reply) is str else bool(reply)

        self.triggers = [t.lower() for e in triggers if (t := e.strip())]
        self.response_text = response_text.strip()
        self.response_images = [
            i for e in response_images if (i := e.replace("\n", "").replace(" ", ""))
        ]
        self.tts = tts
        self.reply = reply


class TriggerSheet:
    """Object for a Google Sheet's spreadsheet containing Discord trigger definitions."""

    triggers: list[SheetTrigger]

    def __init__(self, ss: list[dict[str, str]]):
        self.triggers = [
            SheetTrigger(**self.__parse_row(row)) for row in ss if row["TRIGGERS"]
        ]

    def get_trigger(self, trigger: str) -> SheetTrigger | None:
        """
        Get of a trigger compatible with a given message.

        Parameters
        ----------
        trigger (str): trigger message.

        Returns
        -------
        SheetTrigger | None: the trigger object, if found.
        """
        if not trigger:
            return None

        trigger = trigger.lower()
        for t in self.triggers:
            if trigger in t.triggers:
                return t

    def __parse_row(self, row: dict[str, str]) -> dict[str, str]:
        return {
            "triggers": row["TRIGGERS"],
            "response_text": row["RESPONSE TEXT"],
            "response_images": row["RESPONSE IMAGES"],
            "tts": row["TTS"],
            "reply": row["REPLY"],
        }
