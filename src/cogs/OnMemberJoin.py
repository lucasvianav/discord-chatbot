import pymongo
from discord.ext import commands

import logger
import utils
from config import MONGODB_ATLAS_URI


class onMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        self.db = self.client["discord-bot"]["discord-bot"]

        self.roles = (
            obj["roles"]
            if (obj := self.db.find_one({"description": "onMemberJoinRoles"}))
            else []
        )

    # list all roles that'll be added to new members when they join the server
    @commands.command(
        name="onMemberJoinRoles?",
        aliases=["onMemberJoinRoles"],
        brief="Lista todos os cargos de novos membros.",
        help=(
            "Esse comando lista todos os cargos que serão automaticamente "
            "adicionados a novos membros no momento que eles entrarem no servidor.\n\n"
            "Você pode incluir, remover ou substituir cargos com os comandos `>onMemberJoinRoles+`, "
            "`>onMemberJoinRoles+` e `>onMemberJoinRoles!`, respectivamente."
        ),
    )
    async def listRoles(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>listRolesOMJ` command called.")
        await utils.react_message(ctx.message, ["🐥", utils.MESSAGE_EMOJI, "🚼"])

        response = (
            (
                "`Os cargos que serão dados automaticamente a qualquer um que entrar no servidor são:`\n  * "
                + "\n  * ".join(self.roles)
            )
            if self.roles
            else "No momento, nenhum cargo será dado automaticamente a quem entrar no servidor."
        )
        response += (
            "\n\nNão se esqueça, você pode adicionar ou remover cargos para "
            "serem dados automaticamente a novos membros com os comandos "
            "`>addRolesOMJ` e `>removeRolesOMJ`, respectivamente."
        )

        response = await ctx.send(response)
        await utils.react_response(response)

    # add a new role to be added to new members when they join the server
    @commands.command(
        name="onMemberJoinRoles+",
        brief="Inclui cargos para novos membros.",
        help=(
            "Esse comando só pode ser utilizado por membros da Diretoria e "
            "serve para incluir novos cargos aos que serão adicionados a novos "
            "membros ao entrarem no servidor. É fundamental que o nome do cargo "
            "que você selecionou esteja exatamente igual ele é no Discord.\n\n"
            'Você pode adicionar um ou mais cargos, separando-os com " | " '
            '(caso um dos cargos possua " | " em seu nome, coloque-o como " \\| ").\n'
            'e.g.: ">onMemberJoinRoles+ NOME_CARGO_1 | NOME_CARGO_2 | NOME_CARGO_3"'
        ),
    )
    async def addRoles(self, ctx, *roles):
        await ctx.trigger_typing()
        logger.info("`>addRolesOMJ` command called.")

        roles = utils.parse_piped_list(roles)

        if not utils.in_diretoria(ctx.author) or not roles:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "Apenas membros da diretoria podem utilizar esse comando."
                if roles
                else 'Nenhum nome de cargo foi passado. Para mais informações, envie ">help addRolesOMJ".'
            )
            await utils.react_response(response)

            return

        await utils.react_message(ctx.message, ["🐥", utils.MESSAGE_EMOJI, "🚼"])

        server_roles = [role.name for role in await ctx.guild.fetch_roles()]
        invalid_roles = [role for role in roles if role not in server_roles]
        roles = [role for role in roles if role not in invalid_roles]

        self.roles.extend(roles)
        self.db.find_one_and_update(
            {"description": "onMemberJoinRoles"}, {"$set": {"roles": self.roles}}
        )

        roles = [f'"{role}"' for role in roles]
        response = await ctx.send(
            (
                (
                    f'Os cargos `{", ".join(roles)}` foram incluídos à lista de '
                    "cargos que serão dados a novos membros que entrarem no servidor."
                )
                if roles
                else ""
            )
            + ("\n\n" if roles and invalid_roles else "")
            + (
                (
                    f'Não existem cargos no servidor com nomes `{", ".join(invalid_roles)}` '
                    "e, portanto, eles não foram incluídos. Vale lembrar que você "
                    "deve passar para o comando argumentos exatamente iguais aos "
                    "nomes dos cargos no Discord."
                )
                if invalid_roles
                else ""
            )
        )
        await utils.react_response(response)

    # remove a role from the list to be added to new members when they join the server
    @commands.command(
        name="onMemberJoinRoles-",
        brief="Remove cargos para novos membros.",
        help=(
            "Esse comando só pode ser utilizado por membros da Diretoria e serve "
            "para remover novos cargos dos que serão adicionados a novos membros "
            "ao entrarem no servidor. É fundamental que o nome do cargo que você "
            "selecionou esteja exatamente igual ele é no Discord.\n\n"
            'Você pode remover um ou mais cargos, separando-os com " | " (caso '
            'um dos cargos possua " | " em seu nome, coloque-o como " \\| "). '
            "E, se você não selecionar nenhum cargo, todos serão removido (e "
            "então nenhum cargo será adicionado automaticamente a um novo membro "
            'que entrar no servidor).\ne.g.: ">onMemberJoinRoles- NOME_CARGO_1 | '
            'NOME_CARGO_2 | NOME_CARGO_3"'
        ),
    )
    async def removeRoles(self, ctx, *roles):
        await ctx.trigger_typing()
        logger.info("`>removeRolesOMJ` command called.")

        if not utils.in_diretoria(ctx.author):
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])
            response = await ctx.send(
                "Apenas membros da diretoria podem utilizar esse comando."
            )
            await utils.react_response(response)
            return

        await utils.react_message(ctx.message, ["🐥", utils.MESSAGE_EMOJI, "🚼"])

        roles = utils.parse_piped_list(roles)

        if not roles:
            self.roles = []
            response = (
                "Todos os cargos de onMemberJoin foram removidos!\n\n"
                "Nenhum cargo será automaitcamente dado a membros novos ao entrarem no servidor."
            )
        else:
            invalid_roles = [role for role in roles if role not in self.roles]
            roles = [role for role in roles if role not in invalid_roles]
            self.roles = [role for role in self.roles if role not in roles]

            roles = [f'"{role}"' for role in roles]
            response = (
                ""
                + (
                    f'Os cargos `{", ".join(roles)}` foram removidos da lista '
                    "de cargos que serão dados a novos membros que entrarem no servidor."
                )
                + (
                    f'\n\nJá não existem cargos com nomes `{", ".join(invalid_roles)}` na lista.'
                    if invalid_roles
                    else ""
                )
            )

        self.db.find_one_and_update(
            {"description": "onMemberJoinRoles"}, {"$set": {"roles": self.roles}}
        )
        response = await ctx.send(response)
        await utils.react_response(response)

    # substitute the roles to be added to new members when they join the server
    @commands.command(
        name="onMemberJoinRoles!",
        brief="Substitui os cargos para novos membros.",
        help=(
            "Esse comando só pode ser utilizado por membros da Diretoria e "
            "serve para substituir os cargos que serão adicionados a novos "
            "membros ao entrarem no servidor. É fundamental que o nome do cargo "
            "que você selecionou esteja exatamente igual ele é no Discord.\n\n"
            'Você pode adicionar um ou mais cargos, separando-os com " | " '
            '(caso um dos cargos possua " | " em seu nome, coloque-o como " \\| ").\n'
            'e.g.: ">onMemberJoinRoles! NOME_CARGO_1 | NOME_CARGO_2 | NOME_CARGO_3"'
        ),
    )
    async def substituteRoles(self, ctx, *roles):
        await ctx.trigger_typing()
        logger.info("`>onMemberJoinRoles!` command called.")

        roles = utils.parse_piped_list(roles)

        if not utils.in_diretoria(ctx.author) or not roles:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])
            response = await ctx.send(
                "Apenas membros da diretoria podem utilizar esse comando."
                if roles
                else 'Nenhum nome de cargo foi passado. Para mais informações, envie ">help addRolesOMJ".'
            )
            await utils.react_response(response)
            return

        await utils.react_message(ctx.message, ["🐥", utils.MESSAGE_EMOJI, "🚼"])

        server_roles = [role.name for role in await ctx.guild.fetch_roles()]
        invalid_roles = [role for role in roles if role not in server_roles]
        roles = [role for role in roles if role not in invalid_roles]

        self.roles = roles
        self.db.find_one_and_update(
            {"description": "onMemberJoinRoles"}, {"$set": {"roles": self.roles}}
        )

        roles = [f'"{role}"' for role in roles]
        response = await ctx.send(
            (
                (
                    "A lista de cargos que serão dados a novos membros que "
                    f"entrarem no servidor foi substituída por `{', '.join(roles)}`."
                )
                if roles
                else ""
            )
            + ("\n\n" if roles and invalid_roles else "")
            + (
                (
                    f'Não existem cargos no servidor com nomes `{", ".join(invalid_roles)}` '
                    "e, portanto, eles não foram incluídos. Vale lembrar que você "
                    "deve passar para o comando argumentos exatamente iguais aos "
                    "nomes dos cargos no Discord."
                )
                if invalid_roles
                else ""
            )
        )
        await utils.react_response(response)


def setup(bot):
    bot.add_cog(onMemberJoin(bot))
