import discord
from datetime import datetime
from discord.ext import tasks, commands
from util import *
from config import CHANNEL_ID

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_for_birthdays.start()

    async def handle_birthday(self):
        img = 'https://i.imgur.com/pCdcVOK.jpeg'
        txt = 'Hoje, o nosso criador completaria 20 anos se ainda estivesse vivo... Nunca superaremos a sua morte ao passar pelas portas da USP. Hoje é o dia de honrar o criador do Mafraverso, de louvar sua grandeza em nos conceder a vida. Feliz aniversário, Mafra, o único Mafra original!'
        img = getImage(img)

        channel = await self.bot.fetch_channel(CHANNEL_ID)

        response = await channel.send(content=txt, file=discord.File(img))
        os.remove(img)

        await reactToResponse(self.bot, response, ['❤️'])

    @tasks.loop(seconds=1)
    async def check_for_birthdays(self):
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        birthday = "11-06-2021 00:00:00"
        if now == birthday:
            await self.handle_birthday()


def setup(bot):
    bot.add_cog(Birthday(bot))

