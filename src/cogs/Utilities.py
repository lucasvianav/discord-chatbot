import random
from asyncio import sleep

import discord
from discord.ext import commands
from discord.utils import get

from utilities import logger, utils
from utilities.classes.project import Project


class Utilities(commands.Cog):
    """Commands for general utility functions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=[
            "openProjects",
            "createRole",
            "createRoles",
            "abrirProjeto",
            "abrirProjetos",
            "criarCargo",
            "criarCargos",
        ],
        brief="Auxilia na abertura de um projeto.",
        help=(
            "O self.bot vai enviar uma mensagem convidando os membros a "
            "adicionarem reações para entrarem no projeto. Ele vai esperar 20 "
            "minutos e depois vai criar um cargo para o projeto e adicioná-lo a"
            " todos que reagiram.\n\nÉ possível abrir no mínimo 1 e no máximo 9 "
            'projetos por vez, separando-os por " | ".\ne.g.: ">openProjects '
            'Moletons da Elétrica | Kit Bixo | RPG da SA-SEL"\n\nExiste também '
            "um parâmetro/argumento opcional que pode ser passado para o "
            "comando: se você quiser que eu marque algum cargo, basta "
            'adicionar o parâmetro "$mention=" seguido do nome do cargo a ser '
            "marcado. O nome do cargo a ser marcado deve estar exatamente igual "
            "ao nome do cargo no Discord e esse parâmetro deve ser enviado na "
            "primeira ou na última posição da lista de projetos.\nO parâmetro "
            "é opcional e, se não for fornecido (ou se o cargo fornecido não "
            "for encontrado), nenhum cargo será marcado.\nPor exemplo, se você "
            'incluir "$mention=everyone", eu vou marcar @everyone; se você '
            'incluir "$mention=Moletons da Elétrica" ou "$mention=Moletons", '
            'eu vou marcar "@Moletons da Elétrica" ou "@Moletons", '
            'respectivamente.\ne.g.: ">openProjects Moletons da Elétrica | Kit '
            'Bixo | RPG da SA-SEL | $mention=everyone", ">openProjects '
            "$mention=everyone | Moletons da Elétrica | Kit Bixo | RPG da "
            'SA-SEL"\n\nVale ressaltar que apenas membros da Diretoria podem '
            "abrir projetos."
        ),
    )
    async def openProject(self, ctx, *project_names):
        """
        Send a poll-like message in which users can react to receive a
        role from a list. The role can be created through the command.
        """
        await ctx.trigger_typing()
        logger.info("`>openProject` command called.")

        project_names = utils.parse_piped_list(project_names)
        settings = utils.parse_settings_list(project_names, ["mention"])
        mention_txt, mention = settings["mention"] if settings else None, None

        logger.info(f"The passed projects are: {''.join(project_names)}.", 2)

        if (
            utils.in_diretoria(ctx.author)
            or not project_names
            or len(project_names) > len(utils.AVAILABLE_REACTIONS)
        ):
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                (
                    "Apenas membros da diretoria podem abrir um projeto/criar um cargo."
                    if not utils.in_diretoria(ctx.author)
                    else f"É possível abrir no mínimo 1 e no máximo {len(utils.AVAILABLE_REACTIONS)} projetos ao mesmo tempo."
                )
                + "\nEnvie `>help openProject` para mais informações."
            )
            await utils.react_response(response)

            return

        await utils.react_message(ctx.message, ["🔑", "🚪"])

        if mention_txt:
            mention = await utils.parse_role(mention_txt, ctx.guild)

            if not mention:
                response = await ctx.send(f"O cargo `{mention_txt}` não existe.")
                await utils.react_response(response)
                return
            elif mention_txt.lower() != "everyone":
                mention = mention.mention

        logger.info("The roles are being created.", 2)
        emojis = utils.AVAILABLE_REACTIONS
        random.shuffle(emojis)

        projects = []
        emoji_project = {}
        for p in project_names:
            project = Project(emojis.pop(), ctx.guild)
            await project.process_role(p)
            emoji_project[project.emoji] = project
            projects.append(project)

        sleep_time_minutes = 20
        sleep_time_hours = 12

        projects_message = (
            "`[ABERTURA DE PROJETOS]`\n\n"
            f'{mention if mention_txt else ""}{" " if mention_txt else ""}'
            "Reaja (nesta mensagem) com os respectivos emojis para "
            "ser adicionado aos projetos/cargos a seguir.\n\n"
        ) + "\n".join([f"**{p.name}**: {p.emoji}" for p in projects])

        response = await ctx.send(
            projects_message
            + (
                f"\n\nDaqui a __{sleep_time_minutes} "
                "minutos__, vou criar e adicionar os cargos "
                "a quem já reagiu. Depois disso, pelas "
                f"próximas __{sleep_time_hours} horas__, vou "
                "continuar adicionando cargos a quem reagir,"
                " para caso alguém queira entrar no projeto "
                "depois :)"
            )
        )
        await utils.react_message(response, [p.emoji for p in projects])

        # Sleep for $sleep_time_minutes
        logger.info(
            f"This routine will sleep for {sleep_time_minutes} minutes while it waits for users to react.",
            2,
        )
        await sleep(60 * sleep_time_minutes)

        logger.info("The '>openProject' command is done sleeping.", 1)
        cached_msg = await ctx.fetch_message(response.id)

        # add roles to people who reacted
        await ctx.send("`[PROJETOS ABERTOS]`", delete_after=3600)
        for reaction in cached_msg.reactions:
            if reaction.emoji not in emoji_project.keys():
                continue

            await ctx.trigger_typing()

            project = emoji_project[reaction.emoji]
            project.members.extend(
                [
                    await ctx.guild.fetch_member(user.id)
                    for user in [
                        m for m in await reaction.users().flatten() if not m.bot
                    ]
                ]
            )
            await project.add_role_to_members()

            response = await ctx.send(
                str(project) + "\n\nCargo criado com sucesso!",
                delete_after=3600,
            )
            await utils.react_message(response, reaction.emoji)

        response = await cached_msg.reply(
            f"{mention if mention_txt else ''}{' ' if mention_txt else ''}Vale lembrar "
            "que se você não reagiu anteriormente e quer entrar no projeto, "
            "ainda dá tempo!\n\nQuaisquer pessoas que reajam à messagem de "
            f"abertura dos projetos dentro das próximas **{sleep_time_hours} "
            "horas** receberão os devidos cargos.\n\nLink da mensagem para "
            f"reagir: {cached_msg.jump_url}",
            delete_after=3600,
        )
        await utils.react_response(response)

        # repeats process for the next sleepTime_hours
        logger.info(
            f"This routine will sleep {sleep_time_hours} hours while it monitors new reactions every hour.",
            2,
        )
        for i in range(sleep_time_hours):
            await sleep(3600)  # sleeps for an hour

            logger.info(
                f"The '>openProject' has slept for {i+1} hours. Searching for new reactions...",
                2,
            )
            cached_msg = await ctx.fetch_message(cached_msg.id)

            await cached_msg.edit(
                content=f"{projects_message}\n\nAinda estarei "
                "monitorando essa mensagem por algum tempo, "
                f"você tem mais `{sleep_time_hours-(i+1)} "
                "horas` para reagir."
            )

            # adds the roles to every new member that reacted
            for reaction in cached_msg.reactions:
                if reaction.emoji not in emoji_project.keys():
                    continue

                await ctx.trigger_typing()

                project = emoji_project[reaction.emoji]
                project.members.extend(
                    [
                        await ctx.guild.fetch_member(user.id)
                        for user in [
                            m
                            for m in await reaction.users().flatten()
                            if not m.bot and m not in project.members
                        ]
                    ]
                )
                await project.add_role_to_members()

        await cached_msg.edit(
            content=f"{projects_message}\n\n**Não estou mais "
            "monitorando essa mensagem, portanto não adianta "
            "mais reagir!** Se quiser participar de um dos "
            "projetos, entre em contato com o(a) gerente ou "
            "diretor(a) responsável."
        )

        await ctx.send("`[PROJETOS ABERTOS]`")
        for project in projects:
            response = await ctx.send(str(project))
            await utils.react_message(response, project.emoji)

    @commands.command(
        aliases=["trackpresence", "presença", "registrarPresença", "registrarpresença"],
        brief="Registra presença de membros em reunião.",
        help=(
            "Ajuda a registrar a presença de membros em uma reunião.\n\nAo "
            "enviar '>trackPresence $DURAÇÃO', o self.bot vai monitorar o canal"
            " de voz em que você se encontrava no momento em que enviou a "
            "mensagem por $DURAÇÃO minutos. Ao fim desse tempo, ele vai enviar "
            "uma mensagem com os nomes de todas as pessoas que estiveram no "
            "canal de voz durante.\ne.g.: '>trackPresence 30' vai registrar a "
            "presença por meia hora (30 minutos).\n\nOBS: A $DURAÇÃO deve ser "
            "um número inteiro entre 10 e 120 minutos e, caso não seja "
            "fornecida, o self.bot irá monitorar por uma hora (60 minutos)."
        ),
    )
    async def trackPresence(self, ctx, duration="60"):
        """
        List everybody that (during the duration) stays in the same voice
        channel as the author was originally in for at least a minute.
        """
        await ctx.trigger_typing()

        if not ctx.author.voice:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "É necessário estar conectado em um canal de voz para utilizar esse comando."
            )
            await utils.react_response(response)

            return

        voice_channel = ctx.author.voice.channel
        logger.info(
            f"`>trackPresence` command called on {('the' + voice_channel.name) if voice_channel else 'no'} channel."
        )

        try:
            duration = int(duration)
        except ValueError:
            duration = None

        if not duration or duration < 10 or duration > 120:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "A duração precisa ser um número inteiro entre 10 e 120 minutos."
            )
            await utils.react_response(response)

            return

        await utils.react_message(ctx.message, ["🧮", "⏲️"])

        response = await ctx.send(
            f"{ctx.author.mention} Pode deixar, meu querido! Tô de olho no "
            f"`{voice_channel.name}` pelos próximos `{duration}` minutos :)"
        )
        await utils.react_response(response)

        # people who were in the meeting
        people = []

        # check the channel every minute
        logger.info(
            f"This routine will sleep for {duration} minutes while it monitors the voice channel.",
            2,
        )
        for _ in range(duration):
            people.extend(
                [m for m in voice_channel.members if m not in people and not m.bot]
            )
            await sleep(60)  # sleep for a minute

        logger.info("The '>trackPresence' command is done sleeping.")

        # formatted names of the people who were present
        peoples_names = ", ".join(
            [f"{p.nick} ({p.name})" if p.nick else p.name for p in people]
        )

        response = await ctx.send(
            "`[PRESENÇA DE REUNIÃO]`\n\nRegistro de presença convocado por "
            f"{ctx.author.mention}, no canal de voz `{voice_channel.name}`."
            f"\n\nOs presentes na reunião que começou há `{duration} minutos` "
            f"foram: `{peoples_names}`."
        )
        await utils.react_response(response)

    @commands.command(
        aliases=[],
        brief="Kicka do servidor todos os membros de um cargo (de vdd).",
        help=(
            "Sintaxe: '>kick $CARGO'\n\n$CARGO pode ser tanto o nome do cargo "
            "(exatamente como está escrito no Discord), quanto a mention. Eu "
            "irei kickar do servidor todos os membros que possuem aquele cargo."
            "\nPor exemplo: '>kick Convidado(a)', ou '>members @Convidado(a)'"
            "\n\nOBS: se você quiser que eu retorne a lista dos membros "
            "kickados, inclua '$list' no comando. Por exemplo: '>members "
            "Convidado(a) $list'."
        ),
    )
    async def kick(self, ctx, *argv):
        """Kick all members that have a certain role."""
        await ctx.trigger_typing()

        logger.info("`>kick` command called.")

        if not utils.in_diretoria(ctx.author):
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.reply(
                "Apenas membros da diretoria podem utilizar esse comando. Por "
                f"que você quer kickar os amiguinhos, {ctx.author.mention}? :c"
            )
            await utils.react_response(response)

            return

        await utils.react_message(ctx.message, "🚧")

        argv = " ".join(argv)
        print_list = " $list" in argv
        if print_list:
            argv = argv.replace(" $list", "")

        role = await utils.parse_role(argv, ctx.guild)

        if not argv:
            response = "É necessário fornecer um cargo ao comando. Em caso de dúvidas, envie `>help kick`."
        elif not role:
            response = f"Infelizmente o cargo `{argv}` não existe."
        elif not role.members:
            response = "O cargo não possui nenhum membro."
        else:
            emoji = random.choice(utils.AVAILABLE_REACTIONS)
            sleep_time = 45  # seconds

            response = await ctx.reply(
                "A execução desse comando vai **kickar do servidor** todos os "
                f"`{len(role.members)}` membros do `{role.name}`. Você tem "
                "certeza que deseja prosseguir?\n\nPara continuar o processo, "
                f"reaja nesta mensagem com {emoji} dentro dos próximos `{sleep_time}s`."
            )
            await utils.react_message(response, "❓")

            await sleep(sleep_time)

            cached_msg: discord.message.Message = await ctx.fetch_message(response.id)
            reaction = get(cached_msg.reactions, emoji=emoji)

            if not reaction or not get(
                await reaction.users().flatten(), id=ctx.author.id
            ):
                await cached_msg.reply(
                    f"Como o {ctx.author.mention} não confirmou a continuação do processo, não kickarei ninguém."
                )
                return

            kicked = []
            not_kicked = []

            for member in role.members:
                try:
                    await member.kick(
                        reason="Uso do comando '>kick', por "
                        f"{utils.get_member_name(ctx.author)} no cargo {role.name}."
                    )
                except Exception:
                    not_kicked.append(member)
                else:
                    kicked.append(member)

            def get_member_mention(member):
                return f"{member.mention}"

            kicked = ", ".join(map(get_member_mention, kicked))
            not_kicked = ", ".join(map(get_member_mention, not_kicked))

            response = (
                f"`{len(kicked)}/{len(role.members)}` membros do {role.mention} foram kickados com sucesso."
                + (
                    f"\n\nLista dos membros kickados: {kicked}"
                    if print_list and kicked
                    else ""
                )
                + (
                    f"\n\nLista dos membros não kickados: {not_kicked}"
                    if not_kicked
                    else ""
                )
            )

        response = await ctx.reply(response)
        await utils.react_response(response)

    @commands.command(
        aliases=[],
        brief="Lista todos os membros de um cargo.",
        help=(
            "Sintaxe: '>members $CARGO'\n\n$CARGO pode ser tanto o nome do "
            "cargo (exatamente como está escrito no Discord), quanto a mention."
            " Eu irei retornar a lista de todos os membros que possuem aquele "
            "cargo - o 'apelido' no servidor e o nome de usuário entre "
            "parênteses.\nPor exemplo: '>members Kit Bixo', ou '>members @Kit "
            "Bixo'\n\nOBS: Se você quiser que eu retorne a mention dos membros,"
            " inclua '$mention' no comando. Por exemplo: '>members Kit Bixo "
            "$mention'."
        ),
    )
    async def members(self, ctx, *argv):
        """List all members that have a certain role."""
        await ctx.trigger_typing()

        logger.info("`>members` command called.")
        await utils.react_message(ctx.message, ["⁉️", "ℹ️"])

        argv = " ".join(argv)

        mention = " $mention" in argv
        if mention:
            argv = argv.replace(" $mention", "")

        role = await utils.parse_role(argv, ctx.guild)

        if not argv:
            response = "É necessário fornecer um cargo ao comando. Em caso de dúvidas, envie `>help members`."
        elif not role:
            response = f"Infelizmente o cargo `{argv}` não existe."
        elif not role.members:
            response = "O cargo não possui nenhum membro."
        else:
            members = ", ".join(
                map(
                    (lambda m: f"{m.mention}") if mention else utils.get_member_name,
                    role.members,
                )
            )
            role_name = role.mention if mention else f"`{role.name}`"
            response = (
                f"Os {len(role.members)} membros do {role_name} são:\n\n{members}"
            )

        response = await ctx.reply(response)
        await utils.react_response(response)


def setup(bot):
    bot.add_cog(Utilities(bot))
