from re import search, sub

import discord
import pymongo
from config import MONGODB_ATLAS_URI
from discord.ext import commands, tasks
from discord.utils import get
from util import *
from datetime import datetime
import pytz

ACCEPTABLE_TYPES = {
    "byProject": [ 'project', 'projects', 'projetos', 'projeto', 'reunião', 'reuniões'],
    "byDay": ['day', 'dia', 'dias', 'semana', 'horários']
}

WEEKDAYS = ['Segunda-Feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado', 'Domingo']
CHANNEL_ID = 852293610669342759

formatWeekdays = {
    "segunda": "Segunda-Feira",
    "terça": "Terça-Feira",
    "quarta": "Quarta-Feira",
    "quinta": "Quinta-Feira",
    "sexta": "Sexta-Feira",
    "sábado": "Sábado",
    "domingo": "Domingo"
}

getWeekdayNumber = {
    "segunda": 1,
    "terça": 2,
    "quarta": 3,
    "quinta": 4,
    "sexta": 5,
    "sábado": 6,
    "domingo": 7
}

def sortedMeetings(o):
    return {
        "byProject": {
            project[0]: {
                day[0].title(): sorted(day[1], key=lambda time: int(sub('\D', '', time)))
                for day in sorted(project[1].items(), key=lambda day: getWeekdayNumber[day[0].split('-')[0].lower()])
            }
            for project in sorted(o['byProject'].items(), key=lambda project: project[0])
        },

        "byDay": {
            day[0]: {
                time[0].lower(): sorted(time[1], key=lambda project: project.lower())
                for time in sorted(day[1].items(), key=lambda time: int(sub('\D', '', time[0])))
            }
            for day in sorted(o['byDay'].items(), key=lambda day: getWeekdayNumber[day[0].split('-')[0].lower()])
        }
    }

class Reuniões(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = self.client['discord-bot']['discord-bot']

        self.meetings = sortedMeetings(self.db.find_one({"description": "reuniões"})['meetings'])
        self.remind.start()

    # list of all of the server's meetings
    @commands.command(
        brief='Lista todas as reuniões marcadas.',
        help=f'Esse comando lista todas as reuniões do Zenith que foram marcadas e adicionadas ao bot com o comando ">addMeeting".\n\nVocê pode listar as reuniões ordenadas por dias da semana ou por projetos (padrão). Para ordenar por dias da semana, utilize como argumento para o comando algum dentre a lista {ACCEPTABLE_TYPES["byDay"]} e, para ordenar por projeto, dentre a lista {ACCEPTABLE_TYPES["byProject"]}.\ne.g.: ">meetings day" vai listar as reuniões ordenada por dia e ">meetings project" vai listar as reuniões ordenadas por projetos.',
        aliases=['reuniões', 'reunião', 'meeting', 'listmeetings', 'listarreuniões', 'Meetings', 'Meeting']
    )
    async def meetings(self, ctx, type='project'):
        await ctx.trigger_typing()

        print("\n [*] '>meetings' command called.")

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])

        if type not in ACCEPTABLE_TYPES['byProject'] + ACCEPTABLE_TYPES['byDay']: type = 'day'

        meetingsText = ''

        if type in ACCEPTABLE_TYPES['byProject']:
            for project in self.meetings['byProject'].items():
                meetingsText += f'\n\n{project[0]}'
                for day in project[1].items():
                    for meeting in day[1]: meetingsText += f'\n  • **{day[0]}**: {meeting}'

        else:
            for day in self.meetings['byDay'].items():
                if day[1]:
                    meetingsText += f'\n\n{day[0]}'
                    for time in day[1].items():
                        meetingsText += f'\n  • **{time[0]}**:'
                        for meeting in time[1]: meetingsText += f'\n    ‣ {meeting}'

        txt = f'`As reuniões marcadas (ordenadas por {"dia" if type in ACCEPTABLE_TYPES["byDay"] else "projeto"}) são:`' + meetingsText if meetingsText else 'Não há reuniões marcadas.'
        txt += '\n\nNão se esqueça, você pode marcar ou desmarcar uma reunião com os comandos `>addMeeting` e `>removeMeeting`, respectivamente.' if meetingsText else ''

        response = await ctx.send(txt)

        print('   [**] The response was successfully sent.')

        await reactToResponse(self.bot, response)

    # schedule a new meeting
    @commands.command(
        brief='Adiciona uma nova reunião.',
        help='Formato: $NOME_DO_PROJETO_OU_REUNIÃO | $DIA_DA_REUNIÃO | $HORÁRIO_DA_REUNIÃO\ne.g.: ">addMeeting Reunião Embarcados | Quarta-Feira | 18h15"',
        aliases=['addreunião', 'adicionarreunião', 'addmeeting', 'addReunião', 'adicionarReunião', 'adicionaReunião']
    )
    async def addMeeting(self, ctx, *info):
        await ctx.trigger_typing()

        print("\n [*] '>addMeeting' command called.")

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])

        info = ' '.join(info).split(' | ')
        invalid = False

        if len(info) != 3:
            response = 'Formato inválido. Para entender como funciona o comando, envie `>help addMeeting`.'
            invalid = True

        [meetingName, meetingDay, meetingTime] = info

        try: meetingDay = formatWeekdays[meetingDay.lower()]
        except KeyError: meetingDay = meetingDay.title().replace(' ', '-')

        flag = False

        if meetingDay not in WEEKDAYS:
            response = 'O dia da semana inserido é inválido.'
            invalid = True

        elif not search('\d{2}h\d{2}', meetingTime) or int(sub('\D', '', meetingTime[:2])) > 23:
            response = 'O horário inserido é inválido. Favor inserir no formato "HHhMM", considerando também o formato 24h.\n*e.g.*: "09h15" ou "10h45" ou "15h30" ou "18h00".'
            invalid = True

        if not invalid:
            try:
                if meetingTime in self.meetings['byProject'][meetingName][meetingDay]:
                    response = 'Esse projeto já possui uma reunião marcada nesse horário. Para listar todas as reuniões, envie `>meetings`.'

                else:
                    self.meetings['byProject'][meetingName][meetingDay].append(meetingTime)
                    self.meetings['byDay'][meetingDay][meetingTime].append(meetingName)

                    flag = True
                    response = f"`Reunião marcada com sucesso!`\n**Nome da reunião/projeto**: {meetingName}\n**Dia da reunião**: {meetingDay}\n**Horário da reunião**: {meetingTime}"

            except KeyError:
                try: self.meetings['byProject'][meetingName][meetingDay] = [ meetingTime ]
                except KeyError: self.meetings['byProject'][meetingName] = { meetingDay: [ meetingTime ] }

                try: self.meetings['byDay'][meetingDay][meetingTime] = [meetingName]
                except KeyError: self.meetings['byDay'][meetingDay] = { meetingTime: [ meetingName ] }

                flag = True
                response = f"`Reunião marcada com sucesso!`\n**Nome da reunião/projeto**: {meetingName}\n**Dia da reunião**: {meetingDay}\n**Horário da reunião**: {meetingTime}"

            self.meetings = sortedMeetings(self.meetings)
            self.db.find_one_and_update({"description": "reuniões"}, {"$set": {"meetings": self.meetings}})

        serverRoles = [role.name for role in await ctx.guild.fetch_roles()] + ['Reunião de Diretoria (RD)', 'Reunião Geral (RG)']
        if not meetingName in serverRoles: response += f'\n\n__AVISO__: não existe nenhum cargo chamado "{meetingName}" no servidor.'

        isBadTime = flag and 14 < int(sub('\D', '', meetingTime[:2])) and int(sub('\D', '', meetingTime[:2])) < 18
        if isBadTime: response += f'\n\n*mas vê essa imagem aí e fica esperto(a), malandro(a) {ctx.author.mention}*'
        elif flag and (19 < int(sub('\D', '', meetingTime[:2])) or int(sub('\D', '', meetingTime[:2])) < 12): response += '\n\n*nossa, que horário horrível pra reunião... tô de olho ein!*'
        elif flag and (meetingDay == 'Sábado' or meetingDay == 'Domingo'): response += f'\n\n*isso é crime, ein! {meetingDay.lower()} é dia de descanso, não é dia de reunião não*'

        response = await ctx.send(response) if not isBadTime else await ctx.send(response, file=discord.File('reunião-15h.png'))

        print('   [**] The response was successfully sent.')

        await reactToResponse(self.bot, response)

    # unschedule a new meeting
    @commands.command(
        brief='Remove uma reunião.',
        help='Formato: $NOME_DO_PROJETO_OU_REUNIÃO | $DIA_DA_REUNIÃO | $HORÁRIO_DA_REUNIÃO\ne.g.: ">removeMeeting Reunião Embarcados | Quarta-Feira | 18h15" vai remover a reunião da quarta às 18h15 dos Embarcados.\n\nTambém é possível remover todos os horários/reuniões de um projeto, se apenas o nome desse for informado.\ne.g.: ">removeMeeting Reunião Embarcados" vai remover todas as reuniões dos projetos dos Embarcados.',
        aliases=['removemeeting', 'removerreunião', 'removerReunião', 'removeReunião']
    )
    async def removeMeeting(self, ctx, *info):
        await ctx.trigger_typing()

        print("\n [*] '>removeMeeting' command called.")

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])

        info = ' '.join(info).split(' | ')
        invalid = False

        if len(info) != 1 and len(info) != 3:
            response = 'Formato inválido. Para entender como funciona o comando, envie `>help removeMeeting`.'
            invalid = True

        meetingName = info[0]
        meetingDay = info[1] if len(info) == 3 else None
        meetingTime = info[2] if len(info) == 3 else None

        if meetingDay and meetingTime:
            try: meetingDay = formatWeekdays[meetingDay.lower()]
            except KeyError: meetingDay = meetingDay.title().replace(' ', '-')

            if meetingDay not in WEEKDAYS:
                response = 'O dia da semana inserido é inválido.'
                invalid = True

            elif not search('\d{2}h\d{2}', meetingTime):
                response = 'O horário inserido é inválido. Favor inserir no formato "HHhMM".\n*e.g.*: "09h15" ou "10h45" ou "15h30" ou "18h00".'
                invalid = True

        if not invalid:
            if meetingDay and meetingTime:
                try:
                    if len(self.meetings['byProject'][meetingName][meetingDay]) > 1: self.meetings['byProject'][meetingName][meetingDay].remove(meetingTime)
                    elif len(self.meetings['byProject'][meetingName].keys()) > 1: self.meetings['byProject'][meetingName].pop(meetingDay)
                    else: self.meetings['byProject'].pop(meetingName)

                    if len(self.meetings['byDay'][meetingDay][meetingTime]) > 1: self.meetings['byDay'][meetingDay][meetingTime].remove(meetingName)
                    elif len(self.meetings['byDay'][meetingDay]) > 1: self.meetings['byDay'][meetingDay].pop(meetingTime)
                    else: self.meetings['byDay'].pop(meetingDay)

                except KeyError or ValueError: response = 'O projeto/reunião não foi encontrado. Para ver todas as reuniões marcadas, envie `>meetings`.'

                else: response = 'Reunião desmarcada com sucesso!'

            else:
                try:
                    self.meetings['byProject'].pop(meetingName)

                    removeTimes = []
                    removeDays = []
                    for day in self.meetings['byDay'].keys():
                        for time in self.meetings['byDay'][day].keys():
                            if meetingName in self.meetings['byDay'][day][time]:
                                if len(self.meetings['byDay'][day][time]) > 1: self.meetings['byDay'][day][time].remove(meetingName)
                                elif len(self.meetings['byDay'][day]) > 1: removeTimes.append({"day": day, "time": time})
                                else: removeDays.append(day)

                except KeyError: response = 'O projeto/reunião não foi encontrado. Para ver todas as reuniões marcadas, envie `>meetings`.'

                else:
                    for e in removeTimes: self.meetings['byDay'][e['day']].pop(e['time'])
                    for e in removeDays: self.meetings['byDay'].pop(e)

                    response = 'Reunião desmarcada com sucesso!'

        self.db.find_one_and_update({"description": "reuniões"}, {"$set": {"meetings": self.meetings}})

        response = await ctx.send(response)

        print('   [**] The response was successfully sent.')

        await reactToResponse(self.bot, response)

    # list of all of the author's meetings
    @commands.command(
        brief='Lista todas as reuniões marcadas dos projetos em que você está.',
        help=f'Esse comando lista todas as reuniões dos projetos em que você está (verificação a partir dos cargos) que foram marcadas e adicionadas ao bot com o comando ">addMeeting".\n\nVocê pode listar as reuniões ordenadas por dias da semana (padrão) ou por projetos. Para ordenar por dias da semana, utilize como argumento para o comando algum dentre a lista {ACCEPTABLE_TYPES["byDay"]} e, para ordenar por projeto, dentre a lista {ACCEPTABLE_TYPES["byProject"]}.\ne.g.: ">myMeetings day" vai listar as reuniões ordenada por dia e ">myMeetings project" vai listar as reuniões ordenadas por projetos.',
        aliases=['minhasreuniões', 'minhareunião', 'mymeeting', 'listmymeetings', 'MyMeetings', 'myMeeting', 'mymeetings', 'MyMeeting']
    )
    async def myMeetings(self, ctx, type='day'):
        await ctx.trigger_typing()

        print("\n [*] '>myMeetings' command called.")

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])

        roles = [ role.name for role in ctx.author.roles ]
        if not 'Convidado(a)' in roles: roles += ['Reunião Geral (RG)']
        if 'Diretoria' in roles: roles += ['Reunião de Diretoria (RD)']

        if type not in ACCEPTABLE_TYPES['byProject'] + ACCEPTABLE_TYPES['byDay']: type = 'day'

        meetingsText = ''

        if type in ACCEPTABLE_TYPES['byProject']:
            for project in self.meetings['byProject'].items():
                if project[0] in roles:
                    meetingsText += f'\n\n{project[0]}'
                    for day in project[1].items():
                        for meeting in day[1]: meetingsText += f'\n  • **{day[0]}**: {meeting}'

        else:
            for day in self.meetings['byDay'].items():
                if day[1]:
                    flag = False
                    for role in roles:
                        for e in day[1].values():
                            if role in e:
                                flag = True
                                break

                        if flag: break

                    if flag:
                        meetingsText += f'\n\n{day[0]}'
                        for time in day[1].items():
                            if [e for e in roles if e in time[1]]:
                                meetingsText += f'\n  • **{time[0]}**:'
                                for meeting in time[1]: meetingsText += f'\n    ‣ {meeting}' if meeting in roles else ''

        txt = f'Oi, {ctx.author.mention}!' + (f'\n`As reuniões que você tem marcadas (ordenadas por {"dia" if type in ACCEPTABLE_TYPES["byDay"] else "projeto"}) são:`' + meetingsText) if meetingsText else 'Você não tem reuniões marcadas. Ai, que inveja...'

        response = await ctx.send(txt)

        print('   [**] The response was successfully sent.')

        await reactToResponse(self.bot, response)

    # remider

    @tasks.loop(minutes=1)
    async def remind(self):
        timeZone = pytz.timezone('Etc/GMT+1')
        realTimeZone = pytz.timezone('Etc/GMT+3')

        weekday = datetime.now(timeZone).strftime('%w')
        weekName = WEEKDAYS[int(weekday)]
        print(weekName)
        print('\n')

        now = datetime.now(timeZone).strftime('%Hh%M')
        meetingTime = datetime.now(realTimeZone).strftime('%Hh%M')
        print(f"{now} {meetingTime}\n")

        try:
            reminder = self.meetings['byDay'][weekName][now].items()
            print(reminder)
            print('\n')

            if (reminder):
                print(f"{now} {meetingTime}\n")
                channel = await self.bot.fetch_channel(CHANNEL_ID)
                response = await channel.send(content = f'**Reunião HOJE do {reminder[0]} às {meetingTime}**')
                await reactToResponse (self.bot,response,['🚀'])
        except:
            pass


    # list of all of a role's members' meetings
    @commands.command(
        brief='Fala quais horários os membros de um cargo estão ocupados.',
        help='O comando recebe como argumento o nome de um cargo (exatamente igual está no discord) e vai te avisar em quais horários os membros que possuem aquele cargo estão ocupados (com reuniões do Zenith marcadas).\n\nEx: ">busy Reunião Embarcados".',
        aliases=[]
    )
    async def busy(self, ctx, *roleName):
        print("\n [*] '>busy' command called.")

        await reactToMessage(self.bot, ctx.message, [MESSAGE_EMOJI])
        await ctx.trigger_typing()

        server = ctx.guild
        serverRoles = await server.fetch_roles()
        roleName = ' '.join(roleName)
        role = get(serverRoles, name=roleName)

        if server.default_role == roleName.lower():
            response = ctx.reply('Para isso, use o comando `>meetings`.')
            await reactToResponse(self.bot, response)

        elif not role:
            response = await ctx.send(f'O cargo `{roleName}` não existe.')
            await reactToResponse(self.bot, response)

        else:
            roles = [ r.name for r in set([ member_role for member in role.members for member_role in member.roles ]) ]
            if not 'Convidado(a)' in roles: roles += ['Reunião Geral (RG)']
            if 'Diretoria' in roles: roles += ['Reunião de Diretoria (RD)']

            # Generates the meetings list
            meetingsText = ''
            for day in self.meetings['byDay'].items():
                if day[1]:
                    flag = False
                    for role in roles:
                        for e in day[1].values():
                            if role in e:
                                flag = True
                                break

                        if flag: break

                    if flag:
                        meetingsText += f'\n\n{day[0]}'
                        for time in day[1].items():
                            if [e for e in roles if e in time[1]]:
                                meetingsText += f'\n  • **{time[0]}**:'
                                for meeting in time[1]: meetingsText += f'\n    ‣ {meeting}' if meeting in roles else ''

            txt = f'Oi, {ctx.author.mention}!\n' + (f'\n**As reuniões que os membros do **`{roleName}`** têm marcadas são**:' + meetingsText) if meetingsText else f'Os membros do `{roleName}` não têm reuniões marcadas. Ai, que inveja...'

            response = await ctx.reply(txt)
            print('   [**] The response was successfully sent.')
            await reactToResponse(self.bot, response)

def setup(bot):
    bot.add_cog(Reuniões(bot))
