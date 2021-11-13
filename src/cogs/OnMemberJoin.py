import pymongo
from config import MONGODB_ATLAS_URI
from discord.ext import commands
from util import *

class onMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = self.client['discord-bot']['discord-bot']
        
        self.roles = self.db.find_one({"description": "onMemberJoinRoles"})['roles']

    # list all roles that'll be added to new members when they join the server
    @commands.command(
        brief='Lista todos os cargos de novos membros.',
        help=f'Esse comando lista todos os cargos que serão automaticamente adicionados a novos membros no momento que eles entrarem no servidor.\n\nVocê pode incluir ou remover cargos com os comandos `>addRolesOMJ` e `>removeRolesOMJ`, respectivamente.',
        aliases=['listAutoRoles', 'onMemberJoinRoles', 'onmemberjoinroles', 'listonmemberjoinroles', 'listOnMemberJoinRoles', 'listrolesomj']
    )
    async def listRolesOMJ(self, ctx):
        await ctx.trigger_typing()

        logger.info("`>listRolesOMJ` command called.")

        await utils.react_message(ctx.message, ['🐥', MESSAGE_EMOJI, '🚼'])
                
        response = ('`Os cargos que serão dados automaticamente a qualquer um que entrar no servidor são:`\n  * ' + '\n  * '.join(self.roles)) if self.roles else 'No momento, nenhum cargo será dado automaticamente a quem entrar no servidor.'
        response += '\n\nNão se esqueça, você pode adicionar ou remover cargos para serem dados automaticamente a novos membros com os comandos `>addRolesOMJ` e `>removeRolesOMJ`, respectivamente.'

        response = await ctx.send(response)

        print('   [**] The response was successfully sent.')

        await utils.react_response(response)
        
    # add a new role to be added to new members when they join the server
    @commands.command(
        brief='Inclui cargos para novos membros.',
        help='Esse comando só pode ser utilizado por membros da Diretoria e serve para incluir novos cargos aos que serão adicionados a novos membros ao entrarem no servidor. É fundamental que o nome do cargo que você selecionou esteja exatamente igual ele é no Discord.\n\nVocê pode adicionar um ou mais cargos, separando-os com " | " (caso um dos cargos possua " | " em seu nome, coloque-o como " \| ").\ne.g.: ">addRolesOMJ NOME_CARGO_1 | NOME_CARGO_2 | NOME_CARGO_3"',
        aliases=['addonmemberjoinroles', 'addautoroles', 'addAutoRoles', 'addOnMemberJoinRoles', 'addrolesomj']
    )
    async def addRolesOMJ(self, ctx, *roles):
        await ctx.trigger_typing()

        logger.info("`>addRolesOMJ` command called.")
        
        roles = list(filter(lambda r: r, map(lambda r: r.replace(' \| ', ' | '), ' '.join(roles).split(' | '))))
        
        if 'Diretoria' not in [role.name for role in ctx.author.roles] or not roles:
            await utils.react_message(ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])
        
            response = await ctx.send('Apenas membros da diretoria podem utilizar esse comando.' if roles else 'Nenhum nome de cargo foi passado. Para mais informações, envie ">help addRolesOMJ".')
            await utils.react_response(response)
            
            return

        await utils.react_message(ctx.message, ['🐥', MESSAGE_EMOJI, '🚼'])

        serverRoles = [role.name for role in await ctx.guild.fetch_roles()]
        invalidRoles = list(map(lambda r: f'"{r}"', filter(lambda r: r not in serverRoles, roles)))
        roles = list(filter(lambda r: r in serverRoles, roles))
        
        self.roles.extend(roles)
        roles = list(map(lambda r: f'"{r}"', roles))
        
        self.db.find_one_and_update({"description": "onMemberJoinRoles"}, {"$set": {"roles": self.roles}})

        response = await ctx.send(
            '' + \
            (f'Os cargos `{", ".join(roles)}` foram incluídos à lista de cargos que serão dados a novos membros que entrarem no servidor.' if roles else '') + \
            ('\n\n' if roles and invalidRoles else '') + \
            (f'Não existem cargos no servidor com nomes `{", ".join(invalidRoles)}` e, portanto, eles não foram incluídos. Vale lembrar que você deve passar para o comando argumentos exatamente iguais aos nomes dos cargos no Discord.' if invalidRoles else '')
        )

        print('   [**] The response was successfully sent.')

        await utils.react_response(response)
        
    # remove a role from the list to be added to new members when they join the server
    @commands.command(
        brief='Remove cargos para novos membros.',
        help='Esse comando só pode ser utilizado por membros da Diretoria e serve para remover novos cargos dos que serão adicionados a novos membros ao entrarem no servidor. É fundamental que o nome do cargo que você selecionou esteja exatamente igual ele é no Discord.\n\nVocê pode remover um ou mais cargos, separando-os com " | " (caso um dos cargos possua " | " em seu nome, coloque-o como " \| "). E, se você não selecionar nenhum cargo, todos serão removido (e então nenhum cargo será adicionado automaticamente a um novo membro que entrar no servidor).\ne.g.: ">removeRolesOMJ NOME_CARGO_1 | NOME_CARGO_2 | NOME_CARGO_3"',
        aliases=['removeonmemberjoinroles', 'removeautoroles', 'removeAutoRoles', 'removeOnMemberJoinRoles', 'removerolesomj']
    )
    async def removeRolesOMJ(self, ctx, *roles):
        await ctx.trigger_typing()

        logger.info("`>removeRolesOMJ` command called.")
        
        if 'Diretoria' not in [role.name for role in ctx.author.roles]:
            await utils.react_message(ctx.message, ['🙅‍♂️', '❌', '🙅‍♀️'])
        
            response = await ctx.send('Apenas membros da diretoria podem utilizar esse comando.')
            await utils.react_response(response)
            
            return

        await utils.react_message(ctx.message, ['🐥', MESSAGE_EMOJI, '🚼'])

        roles = list(filter(lambda r: r, map(lambda r: r.replace(' \| ', ' | '), ' '.join(roles).split(' | '))))
        
        if not roles: 
            self.roles = []
            response = 'Todos os cargos de onMemberJoin foram removidos!\n\nNenhum cargo será automaitcamente dado a membros novos ao entrarem no servidor.'

        else:
            invalidRoles = list(map(lambda r: f'"{r}"', filter(lambda r: r not in self.roles, roles)))
            roles = list(filter(lambda r: r in self.roles, roles))
            
            self.roles = list(filter(lambda r: r not in roles, self.roles))
            roles = list(map(lambda r: f'"{r}"', roles))
            
            response = '' + (f'Os cargos `{", ".join(roles)}` foram removidos da lista de cargos que serão dados a novos membros que entrarem no servidor.' if roles else '') + \
                ('\n\n' if roles and invalidRoles else '') + \
                (f'Já não existem cargos com nomes `{", ".join(invalidRoles)}` na lista.' if invalidRoles else '')
        
        self.db.find_one_and_update({"description": "onMemberJoinRoles"}, {"$set": {"roles": self.roles}})

        response = await ctx.send(response)

        print('   [**] The response was successfully sent.')

        await utils.react_response(response)

def setup(bot):
    bot.add_cog(onMemberJoin(bot))
