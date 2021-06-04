import random
from asyncio import sleep
from re import search

import discord
from discord.ext import commands
from discord.utils import get
from util import *

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # sends a poll-like message in which user can react to receive a new role
    @commands.command(
        aliases=['openProjects', 'openproject', 'openprojects', 'createProject', 'createProjects', 'createRole', 'createRoles', 'abrirProjeto', 'createrole', 'createroles', 'abrirprojeto', 'abrirProjetos', 'criarProjeto', 'criarprojeto', 'criarprojetos', 'criarProjetos', 'criarCargo', 'criarCargos', 'criarcargo', 'criarcargos'],
        brief='Auxilia na abertura de um projeto.', 
        help='O self.bot vai enviar uma mensagem convidando os membros a adicionarem reações para entrarem no projeto. Ele vai esperar 20 minutos e depois vai criar um cargo para o projeto e adicioná-lo a todos que reagiram.\n\nÉ possível abrir no mínimo 1 e no máximo 9 projetos por vez, separando-os por " | ".\ne.g.: ">openProjects Garatéa-V | Kurumin | Linux Embarcado"\n\nExiste também um parâmetro/argumento opcional que pode ser passado para o comando: se você quiser que eu marque algum cargo, basta adicionar o parâmetro "$mention=" seguido do nome do cargo a ser marcado. O nome do cargo a ser marcado deve estar exatamente igual ao nome do cargo no Discord e esse parâmetro deve ser enviado na primeira ou na última posição da lista de projetos.\nO parâmetro é opcional e, se não for fornecido (ou se o cargo fornecido não for encontrado), nenhum cargo será marcado.\nPor exemplo, se você incluir "$mention=everyone", eu vou marcar @everyone; se você incluir "$mention=Alto Nível", eu vou marcar "@Alto Nível", respectivamente.\ne.g.: ">openProjects Garatéa-V | Kurumin | Linux Embarcado | $mention=everyone", ">openProjects $mention=everyone | Garatéa-V | Kurumin | Linux Embarcado"\n\nVale ressaltar que apenas Coordenadores podem abrir projetos.'
    )
    async def openProject(self, ctx, *projects):
        await ctx.trigger_typing()

        print('\n [*] \'>openProject\' command called.')
        
        projects = list(filter(lambda project: not search('^\s*$', project), ' '.join(projects).split(' | ')))

        if projects[0].startswith('$mention='):
            mention = projects[0].replace('$mention=', '')
            projects.pop(0)

        elif projects[-1].startswith('$mention='):
            mention = projects[-1].replace('$mention=', '')
            projects.pop(-1)

        else: mention = None
        
        print(f"   [**] The passed projects are: {''.join(projects)}.")

        if 'Coordenador' not in [role.name for role in ctx.author.roles] or len(projects) > len(AVAILABLE_REACTIONS) or len(projects) == 0:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])
        
            response = await ctx.send(('Apenas Coordenadores podem abrir um projeto/criar um cargo.' if 'Coordenador' not in [role.name for role in ctx.author.roles] else f'É possível abrir no mínimo 1 e no máximo {len(AVAILABLE_REACTIONS)} projetos ao mesmo tempo.') + '\nEnvie `>help openProject` para mais informações.')
            await reactToResponse(self.bot, response)
            
            return

        await reactToMessage(self.bot, ctx.message, ['🔑', '🚪'])
        
        server = ctx.guild
        serverRoles = await server.fetch_roles()
        
        if mention: 
            mentionText = mention
            mention = server.default_role if mention.lower() == 'everyone' else get(serverRoles, name=mention)

            if not mention:
                response = await ctx.send(f'O cargo `{mentionText}` não existe.')
                await reactToResponse(self.bot, response)
                return

            elif mentionText.lower() != 'everyone': mention = mention.mention

        # Sleep time in minutes
        sleepTime_minutes = 20
        sleepTime_hours = 12
        
        # Writes message
        reactions = {}
        projects_str = f'`[ABERTURA DE PROJETOS]`\n\n{mention if mention else ""}{" " if mention else ""}Reaja (nesta mensagem) com os respectivos emojis para ser adicionado aos projetos/cargos a seguir.\n'
        for project in projects:
            newReaction = random.choice(AVAILABLE_REACTIONS)
            while newReaction in reactions.values(): newReaction = random.choice(AVAILABLE_REACTIONS)
            
            projects_str += f'\n**{project}**: {newReaction}'
            reactions[project] = newReaction
        response = projects_str + f'\n\nDaqui a __{sleepTime_minutes} minutos__, vou criar e adicionar os cargos a quem já reagiu. Depois disso, pelas próximas __{sleepTime_hours} horas__, vou continuar adicionando cargos a quem reagir, para caso alguém queira entrar no projeto depois :)'
        
        response = await ctx.send(response)

        await reactToMessage(self.bot, response, reactions.values())
        
        # Creates roles
        print(f"   [**] The roles are being created.")
        roles = {
            reactions[project]: await server.create_role(
                name=project, 
                permissions=discord.Permissions(3661376), 
                mentionable=True, 
                reason='Abertura de projeto.'
            ) if project not in [role.name for role in serverRoles] 
            else list(filter(lambda role: project == role.name, serverRoles))[0]
            for project in projects
        }
        print(f"   [**] The roles were successfully created: {', '.join([role.name for role in roles.values()])}.")
        
        # Sleeps for $sleepTime_minutes
        print(f"   [**] This routine will sleep for {sleepTime_minutes} minutes while it waits for users to react.")
        await sleep(60 * sleepTime_minutes)
        print('\n [*] The \'>openProject\' command is done sleeping.')
        
        print(f"   [**] Fetching message reactions.")
        cached = await ctx.fetch_message(response.id)
        print(f"   [**] Fetched message's id: {cached.id}")

        members = {}

        # Adds roles to users who reacted
        await ctx.send('`[PROJETOS ABERTOS]`', delete_after=3600)
        for reaction in cached.reactions:
            if not reaction.emoji in reactions.values(): continue

            await ctx.trigger_typing()

            print(f"   [**] Fetching who reacted {reaction.emoji}.")
            reactors = [await server.fetch_member(user.id) for user in filter(lambda member: not member.bot, await reaction.users().flatten())]

            print(f"   [**] Adding role {roles[reaction.emoji]} to members.")
            for member in reactors: await member.add_roles(roles[reaction.emoji])
            
            print(f'   [**] {roles[reaction.emoji].name} was successfully created and added to the project\'s members.')
            response = await ctx.send(f'**Projeto**: {roles[reaction.emoji].mention}\n**Integrantes** [{len(reactors)}]: {", ".join([member.mention for member in reactors]) if reactors else "poxa, ninguém"}.\n\nCargo criado com sucesso!', delete_after=3600)
            
            await reactToMessage(self.bot, response, [reaction.emoji])
            
            members[reaction.emoji] = list(map(lambda e: e, reactors))
            
        response = await cached.reply(f'{mention if mention else ""}{" " if mention else ""}Vale lembrar que se você não reagiu anteriormente e quer entrar no projeto, ainda dá tempo!\n\nQuaisquer pessoas que reajam à messagem de abertura dos projetos dentro das próximas **{sleepTime_hours} horas** receberão os devidos cargos.\n\nLink da mensagem para reagir: {cached.jump_url}', delete_after=3600)
        await reactToResponse(self.bot, response)

        print(f"   [**] This routine will sleep {sleepTime_hours} hours while it monitors new reactions every hour.")

        # repeats process for the next sleepTime_hours
        for i in range(sleepTime_hours):
            # sleeps for an hour
            await sleep(3600)
            
            print(f'\n [*] The \'>openProject\' has slept for {i+1} hours. Searching for new reactions...')

            # fetches the message again
            cached = await ctx.fetch_message(cached.id)
            print(f"   [**] Fetched message's id: {cached.id}")
            
            await cached.edit(content=f'{projects_str}\n\nAinda estarei monitorando essa mensagem por algum tempo, você tem mais `{sleepTime_hours-(i+1)} horas` para reagir.')

            # adds the roles to every new member that reacted
            for reaction in cached.reactions:
                if not reaction.emoji in reactions.values(): continue

                reactors = [
                    await server.fetch_member(user.id) for user in filter(
                            lambda member: not member.bot and not roles[reaction.emoji].id in [role.id for role in member.roles], 
                            await reaction.users().flatten()
                        )
                ]
                members[reaction.emoji].extend(reactors)

                print(f"   [**] Reactors: {', '.join([member.name for member in reactors])}.")

                for member in reactors: await member.add_roles(roles[reaction.emoji])

        await cached.edit(content=f'{projects_str}\n\n**Não estou mais monitorando essa mensagem, portanto não adianta mais reagir!** Se quiser participar de um dos projetos, entre em contato com o coordenador responsável.')

        await ctx.send('`[PROJETOS ABERTOS]`')
        for reaction in cached.reactions:
            breakpoint()
            response = await ctx.send(f'**Projeto**: {roles[reaction.emoji].mention}\n**Integrantes** [{len(members[reaction.emoji])}]: {", ".join([member.mention for member in members[reaction.emoji]]) if members[reaction.emoji] else "poxa, ninguém"}.')
            await reactToMessage(self.bot, response, [reaction.emoji])

    # lists everybody that stays in the same voice channel as the author for at least 1min
    @commands.command(
        aliases=['trackpresence', 'presença', 'registrarPresença', 'registrarpresença'],
        brief='Registra presença de membros em reunião.',
        help='Ajuda a registrar a presença de membros em uma reunião.\n\nAo enviar ">trackPresence $DURAÇÃO", o self.bot vai monitorar o canal de voz em que você se encontrava no momento em que enviou a mensagem por $DURAÇÃO minutos. Ao fim desse tempo, ele vai enviar uma mensagem com os nomes de todas as pessoas que estiveram no canal de voz durante.\ne.g.: ">trackPresence 30" vai registrar a presença por meia hora (30 minutos).\n\nOBS: A $DURAÇÃO deve ser um número inteiro entre 10 e 120 minutos e, caso não seja fornecida, o self.bot irá monitorar por uma hora (60 minutos).'
    )
    async def trackPresence(self, ctx, duration='60'):
        await ctx.trigger_typing()

        voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
        server = ctx.guild
        
        print(f'\n [*] \'>trackPresence\' command called on {("the" + voiceChannel.name) if voiceChannel else "no"} channel.')

        if not voiceChannel:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])
        
            response = await ctx.send('É necessário estar conectado em um canal de voz para utilizar esse comando.')
            await reactToResponse(self.bot, response)
            
            return
        
        try: duration = int(duration)
        except ValueError: duration = None

        if not duration or duration < 10 or duration > 120:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])
        
            response = await ctx.send('A duração precisa ser um número inteiro entre 10 e 120 minutos.')
            await reactToResponse(self.bot, response)
            
            return

        await reactToMessage(self.bot, ctx.message, ['🧮', '⏲️'])
        
        response = await ctx.send(f'{ctx.author.mention} Pode deixar, meu querido! Tô de olho no `{voiceChannel.name}` pelos próximos `{duration}` minutos :)')
        await reactToResponse(self.bot, response)
        
        # People who were in the meeting
        people = []
        
        # Checks the channel every minute
        print(f"   [**] This routine will sleep for {duration} minutes while it monitors the voice channel.")
        for _ in range(duration):
            voiceChannel = get(server.voice_channels, id=voiceChannel.id)
            people.extend([member.id for member in list(filter(lambda member: not member.id in people, voiceChannel.members))])

            # Sleeps for a minute
            await sleep(60)
            
        print('\n [*] The \'>trackPresence\' command is done sleeping.')

        # Crazy list comprehension that formats all the names
        people = ', '.join([f'{member.nick} ({member.name})' if member.nick else member.name for member in list(filter(lambda member: not member.bot, [await server.fetch_member(id) for id in people]))])
        
        response = await ctx.send(f'`[PRESENÇA DE REUNIÃO]`\n\nRegistro de presença convocado por {ctx.author.mention}, no canal de voz `{voiceChannel.name}`.\n\nOs presentes na reunião que começou há `{duration} minutos` foram: `{people}`.')
        await reactToResponse(self.bot, response)

    # kick all members that have a role (possibly not working)
    @commands.command(
            brief='Kicka do servidor todos os membros de um cargo (de vdd).',
            help='Sintaxe: ">kick $CARGO"\n\n$CARGO pode ser tanto o nome do cargo (exatamente como está escrito no Discord), quanto a mention. Eu irei kickar do servidor todos os membros que possuem aquele cargo.\nPor exemplo: ">kick Convidado(a)", ou ">members @Convidado(a)"\n\nOBS: se você quiser que eu retorne a lista dos membros kickados, inclua "$list" no comando. Por exemplo: ">members Convidado(a) $list".',
            aliases=[]
            )
    async def kick(self, ctx, *argv):
        await ctx.trigger_typing()

        print('\n [*] \'>kick\' command called.')

        if 'Coordenador' not in [role.name for role in ctx.author.roles]:
            await reactToMessage(self.bot, ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])

            response = await ctx.reply(f'Apenas Coordenadores podem utilizar esse comando. Por que você quer kickar os amiguinhos, {ctx.author.mention}? :c')
            await reactToResponse(self.bot, response)

            return

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI, '🚧'])

        argv = " ".join(argv)

        printList = False
        if ' $list' in argv:
            printList = True
            argv = argv.replace(' $list', '')

        role = get(ctx.guild.roles, name=argv)
        if not role: role = get(ctx.guild.roles, mention=argv)

        if not argv: response = 'É necessário fornecer um cargo ao comando. Em caso de dúvidas, envie `>help kick`.'

        elif not role: response = f'Infelizmente o cargo `{argv}` não existe.'

        elif not role.members: response = f'O cargo não possui nenhum membro.'

        else:
            emoji = random.choice(AVAILABLE_REACTIONS)
            sleepTime = 45 # seconds

            response = await ctx.reply(f'A execução desse comando vai **kickar do servidor** todos os `{len(role.members)}` membros do `{argv}`. Você tem certeza que deseja prosseguir?\n\nPara continuar o processo, reaja nesta mensagem com {emoji} dentro dos próximos `{sleepTime}s`.')
            await reactToMessage(self.bot, response, '❓')

            print(f"   [**] This routine will sleep for {sleepTime} seconds whiles it waits for users to react.")
            await sleep(sleepTime)
            print('\n [*] The \'>kick\' command is done sleeping.')

            print(f"   [**] Fetching message reactions.")
            cached = await ctx.fetch_message(response.id)
            print(f"   [**] Fetched message's id: {cached.id}")

            reaction = list(filter(lambda r: emoji == r.emoji, cached.reactions))

            if not reaction or not ctx.author.id in [m.id for m in await reaction[0].users().flatten()]:
                await cached.reply(f'Como o {ctx.author.mention} não confirmou a continuação do processo, não kickarei ninguém.')
                return

            getMemberName = lambda m: f'`{m.nick} ({m.name})`' if m.nick else f'`{m.name}`'
            getMemberMention = lambda m: f'{m.mention}'

            kicked = []
            notKicked = []
            for member in role.members:
                try: await member.kick(reason=f'Uso do comando ">kick", por {getMemberName(ctx.author)} no cargo {argv}.')

                except: notKicked.append(member)

            else: kicked.append(member)

            kicked = ", ".join(map(getMemberMention, kicked))
            notKicked = ", ".join(map(getMemberMention, notKicked))

            response = f'`{len(kicked)} / {len(role.members)}` membros do {role.mention} foram kickados com sucesso.' + \
                    (f'\n\nLista dos membros kickados: {kicked}' if printList and kicked else '') + (f'\n\nLista dos membros não kickados: {notKicked}' if notKicked else '')

        response = await ctx.reply(response)

        await reactToResponse(self.bot, response)

    # list all members that have a role
    @commands.command(
        brief='Lista todos os membros de um cargo.',
        help='Sintaxe: ">members $CARGO"\n\n$CARGO pode ser tanto o nome do cargo (exatamente como está escrito no Discord), quanto a mention. Eu irei retornar a lista de todos os membros que possuem aquele cargo - o "apelido" no servidor e o nome de usuário entre parênteses.\nPor exemplo: ">members Embarcados", ou ">members @Embarcados"\n\nOBS: Se você quiser que eu retorne a mention dos membros, inclua "$mention" no comando. Por exemplo: ">members Embarcados $mention".',
        aliases=['membros', 'whosIn', 'whosin', 'rusin']
    )
    async def members(self, ctx, *argv):
        await ctx.trigger_typing()

        print('\n [*] \'>kick\' command called.')
        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI, '⁉️', 'ℹ️'])

        argv = " ".join(argv)
        
        mention = False
        if ' $mention' in argv:
            mention = True
            argv = argv.replace(' $mention', '')

        role = get(ctx.guild.roles, name=argv)
        if not role: role = get(ctx.guild.roles, mention=argv)
        
        if not argv: response = 'É necessário fornecer um cargo ao comando. Em caso de dúvidas, envie `>help members`.'
            
        elif not role: response = f'Infelizmente o cargo `{argv}` não existe.'
            
        elif not role.members: f'O cargo não possui nenhum membro.'

        else:
            getMemberName = lambda m: f'`{m.nick} ({m.name})`' if m.nick else f'`{m.name}`'
            getMemberMention = lambda m: f'{m.mention}'

            members = ", ".join(map(getMemberMention if mention else getMemberName, role.members))
            roleName = role.mention if mention else f"`{role.name}`"
                
            response = f'Os {len(role.members)} membros do {roleName} são:\n\n{members}'

        response = await ctx.reply(response)

        await reactToResponse(self.bot, response)

def setup(bot):
    bot.add_cog(Utilities(bot))