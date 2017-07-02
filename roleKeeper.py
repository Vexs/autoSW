from discord.ext import commands
import discord
import asyncio
from utils.checks import mod_or_permissions
import json
from utils import checks


class RoleKeeper:
    """"""

    def __init__(self, bot):
        with open('roles.json') as json_file:
            json_data = json.load(json_file)
        self.bot = bot
        self.json_data = json_data
        self.saved_roles = json_data["saving_roles"]
        self.role_dict = json_data["roleme_roles"]

    async def on_member_remove(self, member):
        if member.nick is None or member.nick == member.display_name and not member.roles:
            return
        self.json_data['members'][member.id] = dict(roles=[x.id for x in member.roles if x.id in self.saved_roles],
                                                    nickname='None' if member.nick is None else member.nick,
                                                    name=member.display_name)
        with open('roles.json', 'w') as json_file:
            json_file.write(json.dumps(self.json_data, indent=2))

    async def on_member_join(self, member):
        try:
            member_json = self.json_data['members'].pop(member.id)

            role_list = [discord.Object(id=r_id) for r_id in member_json['roles']]
            await self.bot.add_roles(member, *role_list)

            try:
                if member_json['nickname'] != 'None':
                    await self.bot.change_nickname(member, member_json['nickname'])
            except discord.Forbidden:
                pass

            with open('roles.json', 'w') as json_file:
                json_file.write(json.dumps(self.json_data, indent=2))

        except KeyError:
            pass

    @commands.group(pass_context=True)
    async def rolekeep(self, ctx):
        """The commands group for adding and removing roles to be kept on sever join/leave"""
        if ctx.invoked_subcommand is None:
            role_list = [x.name for x in ctx.message.server.roles if x.id in self.saved_roles]
            await self.bot.say('The following roles are sticky!\n ```{}```'.format('\n'.join(role_list)))

    @rolekeep.group(pass_context=True)
    @checks.is_owner()
    async def clean(self):
        counter = 0
        for key, value in self.json_data['members'].copy().items():
            if value['nickname'] == 'None' or value['nickname'] == value['name'] and not value['roles']:
                self.json_data['members'].pop(key)
                counter += 1
        with open('roles.json', 'w') as json_file:
            json_file.write(json.dumps(self.json_data, indent=2))
        await self.bot.say(counter)

    @rolekeep.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def add(self, ctx, *, role_name: str):
        """The command to add roles to the sticky role list"""
        role = discord.utils.get(ctx.message.server.roles, name=role_name)
        if role is not None:
            if role.id not in self.saved_roles:
                self.json_data['saving_roles'].append(role.id)
                self.saved_roles = self.json_data["saving_roles"]
                with open('roles.json', 'w') as json_file:
                    json_file.write(json.dumps(self.json_data, indent=2))
                await self.bot.say('Added {} to the list of sticky roles!'.format(role_name))
            else:
                await self.bot.say('{} is already sticky!'.format(role_name))
        else:
            await self.bot.say('Unabled to find a role by that name!')

    @rolekeep.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def remove(self, ctx, *, role_name: str):
        """The command to remove roles from the sticky role list"""
        role = discord.utils.get(ctx.message.server.roles, name=role_name)
        if role is not None:
            if role.id in self.saved_roles:
                self.json_data['saving_roles'].remove(role.id)
                self.saved_roles = self.json_data['saving_roles']
                with open('roles.json', 'w') as json_file:
                    json_file.write(json.dumps(self.json_data, indent=2))
                await self.bot.say('Removed {} from the list of sticky roles!'.format(role_name))
            else:
                await self.bot.say('{} is not a sticky role!'.format(role_name))
        else:
            await self.bot.say('Unabled to find a role by that name!')

    @rolekeep.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def list(self, ctx):
        """Lists all the sticky roles"""
        role_list = [x.name for x in ctx.message.server.roles if x.id in self.saved_roles]
        await self.bot.say('The following roles are sticky!\n ```{}```'.format('\n'.join(role_list)))

    @commands.group(pass_context=True, invoke_without_command=True)
    async def roleme(self, ctx, role):
        """Allows you to give yourself an autorole, a list of which can be found by doing "&roleme list"""

        role_obj = next((discord.utils.get(ctx.message.server.roles, id=self.role_dict[key])
                         for key in self.role_dict.keys() if key.lower() == role.lower()), None)
        if role_obj is None:
            await self.bot.say(
                '{} is not a valid roleme, use roleme list to list all available autoroles.'.format(role))
            return
        try:
            await self.bot.add_roles(ctx.message.author, role_obj)
            await self.bot.add_reaction(ctx.message, '✅')
        except discord.Forbidden:
            await self.bot.add_reaction(ctx.message, '❌')
        await asyncio.sleep(10)
        await self.bot.delete_message(ctx.message)

    @roleme.command()
    async def list(self):
        """Lists the avaliable roleme roles!"""
        msg_list = ['The following roles are avaliable for roleme:```']
        for role_name in self.role_dict.keys():
            msg_list.append(role_name)
        msg_list.append('```')
        msg = '\n'.join(msg_list)
        await self.bot.say(msg)

    @roleme.command(pass_context=True)
    async def remove(self, ctx, role):
        """Removes an autorole"""
        role_obj = next((discord.Object(id=self.role_dict[key]) for key in self.role_dict.keys()
                         if key.lower() == role.lower()), None)
        if role_obj is None:
            await self.bot.say(
                '{} is not a valid roleme, use roleme list to list all available autoroles.'.format(role))
            return
        await self.bot.add_reaction(ctx.message, '✅')
        await self.bot.remove_roles(ctx.message.author, role_obj)

    @roleme.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def admin_add(self, ctx, *, rolename):
        """Adds a role to the possible autoroles"""
        role_obj = discord.utils.get(ctx.message.server.roles, name=rolename)
        if role_obj is None:
            await self.bot.say('Unable to find a role by name {}'.format(rolename))
        else:
            if rolename in self.role_dict.keys():
                await self.bot.say('This is already a roleme role!')
                return
            self.json_data['roleme_roles'][rolename] = role_obj.id
            with open('roles.json', 'w') as json_file:
                json_file.write(json.dumps(self.json_data, indent=2))
            await self.bot.say('Added {} to the list of roleme roles!'.format(rolename))

    @roleme.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def admin_remove(self, ctx, *, rolename):
        """Adds a role to the possible autoroles"""
        role_obj = discord.utils.get(ctx.message.server.roles, name=rolename)
        if role_obj is None:
            await self.bot.say('Unable to find a role by name {}'.format(rolename))
        else:
            if rolename not in self.role_dict.keys():
                await self.bot.say('This is not a roleme role!')
                return
            self.json_data['roleme_roles'].pop(rolename)
            with open('roles.json', 'w') as json_file:
                json_file.write(json.dumps(self.json_data, indent=2))
            await self.bot.say('Removed {} from the list of roleme roles!'.format(rolename))


def setup(bot):
    bot.add_cog(RoleKeeper(bot))
