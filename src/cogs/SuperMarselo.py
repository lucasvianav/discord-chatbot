import random
from asyncio import sleep

from discord import File
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located as presence,
)
from selenium.webdriver.support.ui import WebDriverWait as waiter
from webdriver_manager.chrome import ChromeDriverManager

from utilities import logger, utils


class SuperMarselo(commands.Cog):
    """Crazy random commands."""

    def __init__(self, bot):
        self.bot = bot
        self.CHROME_DRIVER = ChromeDriverManager().install()

    @commands.command(
        brief="Separa os times pro famigerado.",
        help=(
            "Esse comando separa dois times para jogar codenames, já "
            "selecionando quem vai ser o spymaster de cada time.\n\nSe você "
            "quiser, ele pode, ainda, criar uma sala de Codenames e enviar o "
            "link. Para isso, adicione um dos argumentos a seguir: "
            '"$createRoom=true", "$createRoom", "True", "createRoom", '
            '"criarSala", "link", "URL", "URI".\ne.g.: ">codenames '
            '$createRoom=True", ou ">codenames True", ou ">codenames link", '
            "etc.\n\nÉ necessário estar conectado a um canal de voz com pelo "
            "menos mais três pessoas para ativar esse comando."
        ),
    )
    async def codenames(self, ctx, createRoom=None):
        """Create a Codenames room."""
        await ctx.trigger_typing()
        logger.info("`>codenames` command called.")

        voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
        members = [m for m in voiceChannel.members if not m.bot] if voiceChannel else []

        if not voiceChannel or len(members) < 4:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "É necessário estar em um canal de voz para usar esse comando."
                if not voiceChannel
                else "É necessário no mínimo 4 pessoas para jogar Codenames."
            )
            await utils.react_response(response)

            return
        else:
            await utils.react_message(ctx.message, ["🎲", "🎮", "🏏", "🕹️"])

        createRoom = createRoom and createRoom.lower() in [
            "$createroom=true",
            "$createroom",
            "true",
            "createroom",
            "criarsala",
            "link",
            "url",
            "uri",
        ]

        logger.info(f"{len(members)} members are present.", 2)
        logger.info(f'A room will {"" if createRoom else "not"} be created.', 2)

        people = [member.mention for member in members]

        blueSpymaster = random.choice(people)
        people.remove(blueSpymaster)

        redSpymaster = random.choice(people)
        people.remove(redSpymaster)

        blueOperatives = []
        for _ in range(len(people) // 2):
            blueOperatives.append(random.choice(people))
            people.remove(blueOperatives[-1])

        redOperatives = people

        logger.info("The teams were created.", 2)

        if createRoom:
            logger.info("A room is being created.", 2)

            opt = webdriver.ChromeOptions()
            opt.add_argument("--headless")
            opt.add_argument("--disable-dev-shm-usage")
            opt.add_argument("--disable-gpu")
            opt.add_argument("--no-sandbox")
            opt.add_argument("--disable-extensions")

            logger.info("Opening the website...", 2)

            driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER, options=opt)
            driver.get("https://codenames.game/room/create")

            try:
                await ctx.trigger_typing()

                waiter(driver, 10, poll_frequency=0.1).until(
                    presence(
                        (By.XPATH, '//h1[contains(text(), "Welcome to Codenames")]')
                    )
                )

                logger.info("Waiting for the website to load...", 2)

                driver.find_element_by_xpath('//input[@id="nickname-input"]').send_keys(
                    "A Voz da SA-SEL"
                )
                driver.find_element_by_xpath(
                    '//button[contains(text(), "Create Room") and contains(@type, "submit")]'
                ).click()

                logger.info("Setting up the game...", 2)

                waiter(driver, 10, poll_frequency=0.1).until(
                    presence((By.XPATH, '//span[contains(text(), "Set up a game")]'))
                )

                driver.find_element_by_xpath(
                    '//div[contains(@class, "flag") and contains(@class, "pt")]'
                ).click()

                driver.find_element_by_xpath(
                    '//button[contains(text(), "Start New Game")]'
                ).click()

                logger.info("Waiting for the room to be created...", 2)

                waiter(driver, 10, poll_frequency=0.1).until(
                    presence(
                        (
                            By.XPATH,
                            '//div[contains(text(), "A Voz da SA-SEL") and contains(@class, "button-inner")]',
                        )
                    )
                )
            except Exception:
                roomURL = None
                driver.quit()
            else:
                roomURL = driver.current_url
        else:
            roomURL = None
            driver = None

        response = await ctx.send(
            "`TÁ NA HORA DO CODENAMES GAROTADA`\n\n"
            + (f"**Link da sala**: {roomURL}\n\n" if roomURL else "")
            + f"**Time azul**  🔵:\n__*Spymaster*__: {blueSpymaster}\n"
            + f'__*Operatives*__: {", ".join(blueOperatives)}\n\n**Time '
            + f"vermelho**  🔴:\n__*Spymaster*__: {redSpymaster}\n"
            + f'__*Operatives*__: {", ".join(redOperatives)}\n\n'
            + "Que vença o melhor time!"
        )
        await utils.react_response(response)

        # if a room was created, the bot needs
        # to leave it after someone entered
        if driver:
            await sleep(180)
            await ctx.trigger_typing()

            try:
                people = (
                    [blueSpymaster] + blueOperatives + [redSpymaster] + redOperatives
                )

                try:
                    driver.find_element_by_xpath(
                        '//button//span[text()="Players"]'
                    ).click()

                    newHost = driver.find_element_by_xpath(
                        '//div[@class="relative"]//span[contains(@class, "bg-green-online") and contains(@class, '
                        '"rounded-full")]/following-sibling::span[not(contains(text(), "A Voz da SA-SEL"))]'
                    )

                    newHost.click()
                    waiter(driver, 5, poll_frequency=0.1).until(
                        presence(
                            (By.XPATH, '//button[contains(text(), "Make a Host")]')
                        )
                    ).click()
                except Exception:
                    response = await ctx.send(
                        f"Alô, {ctx.author.mention}! Eu vou sair da sala, mas como ninguém mais entrou, a sala vai ficar sem host. "
                        f'Se quiserem que crie outra sala depois, é só chamar.\n\ncc: {" ".join(people)}'
                    )
                else:
                    response = await ctx.send(
                        f'Alô, {ctx.author.mention}! Eu vou sair da sala, agora **o novo host é o `{newHost.text}`**.\n\ncc: {" ".join(people)}'
                    )
                finally:
                    await utils.react_response(response)

                driver.find_element_by_xpath(
                    '//div[contains(text(), "A Voz da SA-SEL") and contains(@class, "button-inner")]'
                ).click()
                waiter(driver, 5, poll_frequency=0.1).until(
                    presence((By.XPATH, '//div[text()="Leave the Room"]'))
                ).click()
            finally:
                await sleep(3)
                driver.quit()

    @commands.command(brief="Press F to pay respects.")
    async def F(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>F` command called.")
        await utils.react_message(ctx.message, "⚰")
        response = await ctx.send("`Press F to Pay Respects`")
        await utils.react_response(response)

    @commands.command(brief="Chama um membro.", aliases=["cade", "kd"])
    async def cadê(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>cadê` command called.")
        await utils.react_message(ctx.message, ["🤬"])
        response = await ctx.send(
            f"**cadê vc otário??** {' '.join(user)}", file=File("images/cade-vc.png")
        )
        await utils.react_response(response, ["❔"])

    @commands.command(brief='"Bane" um "usuário" do servidor.')
    async def ban(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>ban` command called.")
        await utils.react_message(ctx.message, ["👺"])
        response = await ctx.send(f"O usuário '{' '.join(user)}' foi banido.")
        await utils.react_response(response, ["💀"])

    @commands.command(brief="Declara a saideira!")
    async def saideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>saideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            f"A saideira do {ctx.author.mention} está oficialmente declarada! "
            "A próxima partida será a última dele. Em caso de saideira de "
            'conversa, "a próxima partida" equivale aos próximos 30 minutos '
            "de um bom papo. \n\nPara mais informações, acione o comando "
            "`>regrasSaideira`."
        )
        await utils.react_response(response)

    @commands.command(
        brief="Regras relacionadas à saideira.",
        aliases=["regrassaideira", "regrasaideira"],
    )
    async def regrasSaideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>regrasSaideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            "**A REGRA É CLARA!**\n\nA saideira precisa ser previamente "
            "declarada com uso do comando `>saideira`. Caso contrário, a "
            "saideira é inválida e todos têm direito de acionar o comando "
            "`>kakashi` para quem descumpriu a regra.\n\nA partir do momento "
            "em que a saideira for declarada, o declarante deve continuar "
            "jogando por no mínimo mais uma (01) partida e, no máximo, duas "
            "(02) - depois desse tempo, a saideira expira e deverá ser "
            "declarada novamente. Vale lembrar, que a 'partida' da saideira de "
            "conversa equivale a 30 minutos de um bom papo."
        )
        await utils.react_response(response)


def setup(bot):
    bot.add_cog(SuperMarselo(bot))
