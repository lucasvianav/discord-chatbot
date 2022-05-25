from discord import Guild, Member, Permissions, Role
from discord.utils import get

from utilities import logger


class Project:
    __role: Role

    server: Guild
    name: str
    emoji: str
    members: list[Member]

    def __init__(self, emoji: str, server: Guild):
        self.server = server
        self.emoji = emoji
        self.members = []

    def __str__(self) -> str:
        return (
            f"**Projeto**: {self.emoji} {self.__role.mention}\n**Integrantes** [{len(self.members)}]: "
            f"{', '.join([m.mention for m in self.members]) if self.members else 'poxa, ninguém'}."
        )

    async def process_role(self, r: str) -> None:
        role: Role = (
            get(self.server.roles, name=r)
            or (r.startswith("@") and get(self.server.roles, mention=r))
            or await self.server.create_role(
                name=r,
                permissions=Permissions(3661376),
                mentionable=True,
                reason="Abertura de projeto.",
            )
        )
        logger.info(
            f"{self.__role.name} was successfully created/retrieved.",
            2,
        )
        self.__role = role
        self.name = self.__role.name
        self.members = self.__role.members

    async def add_role_to_members(self) -> None:
        for member in [m for m in self.members if self.__role not in m.roles]:
            await member.add_roles(self.__role)
        logger.info(
            f"{self.__role.name} was successfully added to the project's members.",
            2,
        )
