import random
from asyncio import sleep
from re import search

import discord
from discord.ext import commands
from discord.utils import get

import logger
import utils


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # sends a poll-like message in which user can react to receive a new role
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
    async def openProject(self, ctx, *projects):
        await ctx.trigger_typing()
        logger.info("`>openProject` command called.")

        projects = utils.parse_piped_list(projects)
        projects = [p for p in projects if not search(r"^\s*$", p)]

        settings = utils.parse_settings_list(projects, ["mention"])
        mention_txt, mention = settings["mention"] if settings else None, None

        logger.info(f"The passed projects are: {''.join(projects)}.", 2)

        if (
            utils.in_diretoria(ctx.author)
            or not projects
            or len(projects) > len(utils.AVAILABLE_REACTIONS)
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

        server = ctx.guild
        server_roles = await server.fetch_roles()

        if mention_txt:
            mention = await utils.parse_role(mention_txt, ctx)

            if not mention:
                response = await ctx.send(f"O cargo `{mention_txt}` não existe.")
                await utils.react_response(response)
                return
            elif mention_txt.lower() != "everyone":
                mention = mention.mention

        # sleep time in minutes
        sleep_time_minutes = 20
        sleep_time_hours = 12

        reactions = {}  # { [project]: reaction }
        projects_str = (
            "`[ABERTURA DE PROJETOS]`\n\n"
            f'{mention if mention_txt else ""}{" " if mention_txt else ""}'
            "Reaja (nesta mensagem) com os respectivos emojis para "
            "ser adicionado aos projetos/cargos a seguir.\n"
        )

        # adds a reaction for each project
        for project in projects:
            new_reaction = random.choice(
                [r for r in utils.AVAILABLE_REACTIONS if r not in reactions.values()]
            )
            projects_str += f"\n**{project}**: {new_reaction}"
            reactions[project] = new_reaction

        response = projects_str + (
            f"\n\nDaqui a __{sleep_time_minutes} "
            "minutos__, vou criar e adicionar os cargos "
            "a quem já reagiu. Depois disso, pelas "
            f"próximas __{sleep_time_hours} horas__, vou "
            "continuar adicionando cargos a quem reagir,"
            " para caso alguém queira entrar no projeto "
            "depois :)"
        )

        response = await ctx.send(response)
        await utils.react_message(response, list(reactions.values()))

        logger.info("The roles are being created.", 2)
        roles = {
            reactions[project]: get(server_roles, name=project)
            or await server.create_role(
                name=project,
                permissions=discord.Permissions(3661376),
                mentionable=True,
                reason="Abertura de projeto.",
            )
            for project in projects
        }
        logger.info(
            f"The roles were successfully created: {', '.join([role.name for role in roles.values()])}.",
            2,
        )

        # Sleep for $sleep_time_minutes
        logger.info(
            f"This routine will sleep for {sleep_time_minutes} minutes while it waits for users to react.",
            2,
        )
        await sleep(60 * sleep_time_minutes)
        logger.info("The '>openProject' command is done sleeping.", 1)

        logger.info("Fetching message reactions.", 2)
        cached_msg = await ctx.fetch_message(response.id)
        logger.info(f"Fetched message's id: {cached_msg.id}", 2)

        members = {}  # { [reaction_emoji]: members_in_project }

        def get_project_report(reaction: discord.Reaction) -> str:
            """
            Parameters
            ----------
            reaction (discord.Reaction): the reaction that represents the project.

            Returns
            -------
            str: text listing that project's members.
            """
            return (
                f"**Projeto**: {reaction.emoji} {roles[reaction.emoji].mention}"
                f"\n**Integrantes** [{len(members[reaction.emoji])}]: "
                f"{', '.join([member.mention for member in members[reaction.emoji]]) if members[reaction.emoji] else 'poxa, ninguém'}."
            )

        # add roles to users who reacted
        await ctx.send("`[PROJETOS ABERTOS]`", delete_after=3600)
        for reaction in cached_msg.reactions:
            if reaction.emoji not in reactions.values():
                continue

            await ctx.trigger_typing()

            logger.info(f"Fetching who reacted {reaction.emoji}.", 2)
            members_reacted = [
                await server.fetch_member(user.id)
                for user in [m for m in await reaction.users().flatten() if not m.bot]
            ]
            logger.info(f"Adding role {roles[reaction.emoji]} to members.", 2)

            for member in members_reacted:
                await member.add_roles(roles[reaction.emoji])
            logger.info(
                f"{roles[reaction.emoji].name} was successfully created and added to the project's members.",
                2,
            )

            members[reaction.emoji] = members_reacted

            response = await ctx.send(
                get_project_report(reaction) + "\n\nCargo criado com sucesso!",
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

            # fetches the message again
            cached_msg = await ctx.fetch_message(cached_msg.id)
            await cached_msg.edit(
                content=f"{projects_str}\n\nAinda estarei "
                "monitorando essa mensagem por algum tempo, "
                f"você tem mais `{sleep_time_hours-(i+1)} "
                "horas` para reagir."
            )

            # adds the roles to every new member that reacted
            for reaction in cached_msg.reactions:
                if reaction.emoji not in reactions.values():
                    continue

                members_reacted = [
                    await server.fetch_member(user.id)
                    for user in [
                        m
                        for m in await reaction.users().flatten()
                        if not m.bot and not roles[reaction.emoji].id in m.roles
                    ]
                ]

                for member in members_reacted:
                    await member.add_roles(roles[reaction.emoji])

                members[reaction.emoji].extend(members_reacted)
                logger.info(
                    f"Reactors: {', '.join([member.name for member in members_reacted])}.",
                    2,
                )

        await cached_msg.edit(
            content=f"{projects_str}\n\n**Não estou mais "
            "monitorando essa mensagem, portanto não adianta "
            "mais reagir!** Se quiser participar de um dos "
            "projetos, entre em contato com o(a) gerente ou "
            "diretor(a) responsável."
        )

        await ctx.send("`[PROJETOS ABERTOS]`")
        for reaction in cached_msg.reactions:
            response = await ctx.send(get_project_report(reaction))
            await utils.react_message(response, reaction.emoji)

    # lists everybody that stays in the same voice channel as the author for at least 1min
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

    # kick all members that have a role (possibly not working)
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

        role = await utils.parse_role(argv, ctx)

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

    # list all members that have a role
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
        await ctx.trigger_typing()

        logger.info("`>members` command called.")
        await utils.react_message(ctx.message, ["⁉️", "ℹ️"])

        argv = " ".join(argv)

        mention = " $mention" in argv
        if mention:
            argv = argv.replace(" $mention", "")

        role = await utils.parse_role(argv, ctx)

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
