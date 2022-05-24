from typing import Any

import discord
from discord import Message
from discord.ext.commands.context import Context

from utilities import logger, utils


class SheetDiscordInteraction:
    """Base class for commands and triggers."""

    response_text: str
    response_images: list[str]
    tts: bool
    reply: bool

    def get_content(self) -> tuple[dict[str, Any], list[str]]:
        """Return a dict with the trigger's content to be passed directly into a Discord's `send()` method."""
        kwargs = {"content": self.response_text, "tts": self.tts}

        images = utils.get_images(self.response_images)

        if images:
            kwargs["files"] = [discord.File(img) for img in images]

        return kwargs, images

    async def send(
        self, ctx: Message | Context, emoji: str | list[str] = utils.RESPONSE_EMOJI
    ) -> Message:
        """
        Fire the trigger, sending it's contents to a message's channel/context.
        Also react to the sent message with given emoji.

        Parameters
        ----------
        ctx (Message | Context): either a message or a context to sent the trigger's contents in (if message, in it's channel).
        emoji (str | list[str]): emoji to react to the sent message with.

        Returns
        -------
        Message: the triggers message.
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
