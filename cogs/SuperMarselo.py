import random
from asyncio import sleep

from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import \
    presence_of_element_located as presence
from selenium.webdriver.support.ui import WebDriverWait as waiter
from webdriver_manager.chrome import ChromeDriverManager

from util import *


class SuperMarselo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHROME_DRIVER = ChromeDriverManager().install()

    # Separates everyone on the author's voice channel into teams
    # and creates a Codenames room in portuguese
    @commands.command(
        brief='Separa os times pro famigerado.',
        help='Esse comando separa dois times para jogar codenames, já selecionando quem vai ser o spymaster de cada time.\n\nSe você quiser, ele pode, ainda, criar uma sala de Codenames e enviar o link. Para isso, adicione um dos argumentos a seguir: "$createRoom=true", "$createRoom", "True", "createRoom", "criarSala", "link", "URL", "URI".\ne.g.: ">codenames $createRoom=True", ou ">codenames True", ou ">codenames link", etc.\n\nÉ necessário estar conectado a um canal de voz com pelo menos mais três pessoas para ativar esse comando.'
    )
    async def codenames(self, ctx, createRoom=None):
        await ctx.trigger_typing()

        print('\n [*] \'>codenames\' command called.')

        voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
        if not voiceChannel or len(list(filter(lambda member: not member.bot, voiceChannel.members))) < 4:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])

            response = await ctx.send('É necessário estar conectado em um canal de voz para utilizar esse comando.' if not voiceChannel else 'É necessário no mínimo 4 pessoas para jogar Codenames.')
            await reactToResponse(self.bot, response)

            return

        else: await reactToMessage(self.bot, ctx.message, ['🎲', '🎮', '🏏', '🕹️'])

        createRoom = True if createRoom and createRoom.lower() in ['$createroom=true', '$createroom', 'true', 'createroom', 'criarsala', 'link', 'url', 'uri'] else False

        print(f'   [**] A room will {"" if createRoom else "not"} be created.')

        people = [member.mention for member in list(filter(lambda member: not member.bot, voiceChannel.members))]

        print(f'   [**] {len(people)} members are present.')

        blueSpymaster = random.choice(people)
        people.remove(blueSpymaster)

        redSpymaster = random.choice(people)
        people.remove(redSpymaster)

        blueOperatives = []
        for _ in range(int(len(people)/2)):
            blueOperatives.append(random.choice(people))
            people.remove(blueOperatives[-1])

        redOperatives = people

        print(f'   [**] The teams were created.')

        if createRoom:
            print(f'   [**] A room is being created.')

            opt = webdriver.ChromeOptions()
            opt.add_argument('--headless')
            opt.add_argument("--disable-dev-shm-usage")
            opt.add_argument('--disable-gpu')
            opt.add_argument('--no-sandbox')
            opt.add_argument("--disable-extensions")

            print(f'   [**] Opening the website...')

            driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER, options=opt)
            driver.get('https://codenames.game/room/create')

            try:
                await ctx.trigger_typing()

                waiter(driver, 10, poll_frequency=0.1).until(presence((By.XPATH, '//h1[contains(text(), "Welcome to Codenames")]')))

                print(f'   [**] Waiting for the website to load...')

                driver.find_element_by_xpath('//input[@id="nickname-input"]').send_keys('A Voz da SA-SEL')
                driver.find_element_by_xpath('//button[contains(text(), "Create Room") and contains(@type, "submit")]').click()

                print(f'   [**] Setting up the game...')

                waiter(driver, 10, poll_frequency=0.1).until(presence((By.XPATH, '//span[contains(text(), "Set up a game")]')))

                driver.find_element_by_xpath('//div[contains(@class, "flag") and contains(@class, "pt")]').click()

                # Uncomment below to activate Brazil's expansion pack
                # driver.find_element_by_xpath('//input[contains(@id, "Expansão promocional: Brasil") and contains(@type, "checkbox") and contains(@name, "Expansão promocional: Brasil")]').click()

                driver.find_element_by_xpath('//button[contains(text(), "Start New Game")]').click()

                print(f'   [**] Waiting for the room to be created...')

                waiter(driver, 10, poll_frequency=0.1).until(presence((By.XPATH, '//div[contains(text(), "A Voz da SA-SEL") and contains(@class, "button-inner")]')))

            except:
                roomURL = None
                driver.quit()

            else: roomURL = driver.current_url

        else: roomURL = None

        response = await ctx.send('`TÁ NA HORA DO CODENAMES GAROTADA`\n\n' + (f'**Link da sala**: {roomURL}\n\n' if roomURL else '') + f'**Time azul**  🔵:\n__*Spymaster*__: {blueSpymaster}\n__*Operatives*__: {", ".join(blueOperatives)}\n\n**Time vermelho**  🔴:\n__*Spymaster*__: {redSpymaster}\n__*Operatives*__: {", ".join(redOperatives)}\n\nQue vença o melhor time!')
        await reactToResponse(self.bot, response)

        if roomURL:
            # Sleeps for 3 minute
            await sleep(180)

            await ctx.trigger_typing()

            try:
                people = [blueSpymaster] + blueOperatives + [redSpymaster] + redOperatives
                people.remove(ctx.author.mention)

                try:
                    driver.find_element_by_xpath('//button//span[text()="Players"]').click()

                    newHost = driver.find_element_by_xpath('//div[@class="relative"]//span[contains(@class, "bg-green-online") and contains(@class, "rounded-full")]/following-sibling::span[not(contains(text(), "A Voz da SA-SEL"))]')

                    newHost.click()
                    waiter(driver, 5, poll_frequency=0.1).until(presence((By.XPATH, '//button[contains(text(), "Make a Host")]'))).click()

                except: response = await ctx.send(f'Alô, {ctx.author.mention}! Eu vou sair da sala, mas como ninguém mais entrou, a sala vai ficar sem host. Se quiserem que crie outra sala depois, é só chamar.\n\ncc: {" ".join(people)}')

                else: response = await ctx.send(f'Alô, {ctx.author.mention}! Eu vou sair da sala, agora **o novo host é o `{newHost.text}`**.\n\ncc: {" ".join(people)}')

                finally: await reactToResponse(self.bot, response)

                driver.find_element_by_xpath('//div[contains(text(), "A Voz da SA-SEL") and contains(@class, "button-inner")]').click()
                waiter(driver, 5, poll_frequency=0.1).until(presence((By.XPATH, '//div[text()="Leave the Room"]'))).click()

            finally:
                await sleep(3)
                driver.quit()

    @commands.command(
        brief='Declara a saideira!',
        help='',
        aliases=['Saideira']
    )
    async def saideira(self, ctx):
        await ctx.trigger_typing()

        print('\n [*] \'>saideira\' command called.')
        await reactToMessage(self.bot, ctx.message, ['🍉', '🚩'])

        response = await ctx.reply(f"A saideira do {ctx.author.mention} está oficialmente declarada! A próxima partida será a última dele. Em caso de saideira de conversa, \"a próxima partida\" equivale aos próximos 30 minutos de um bom papo. \n\nPara mais informações, acione o comando `>regrasSaideira`.")

        await reactToResponse(self.bot, response)

    @commands.command(
        brief='Regras relacionadas à saideira.',
        help='',
        aliases=['regrassaideira', 'regrasaideira']
    )
    async def regrasSaideira(self, ctx):
        await ctx.trigger_typing()

        print('\n [*] \'>saideira\' command called.')
        await reactToMessage(self.bot, ctx.message, ['🍉', '🚩'])

        response = await ctx.reply("**A REGRA É CLARA!**\n\nA saideira precisa ser previamente declarada com uso do comando `>saideira`. Caso contrário, a saideira é inválida e todos têm direito de acionar o comando `>kakashi` para quem descumpriu a regra.\n\nA partir do momento em que a saideira for declarada, o declarante deve continuar jogando por no mínimo mais uma (01) partida e, no máximo, duas (02) - depois desse tempo, a saideira expira e deverá ser declarada novamente. Vale lembrar, que a \"partida\" da saideira de conversa equivale a 30 minutos de um bom papo.")

        await reactToResponse(self.bot, response)

def setup(bot):
    bot.add_cog(SuperMarselo(bot))

