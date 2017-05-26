from discord.ext import commands
import discord
import asyncio
from utils.checks import mod_or_permissions
import json

class roleKeeper:
    """"""
    def __init__(self, bot):
        with open('roles.json') as json_file:
            json_data = json.load(json_file)
        self.bot = bot
        self.json_data = json_data
        self.saved_roles = json_data["saving_roles"]


    async def on_member_remove(self, member):
        if member.nick is None and len(member.roles) == 0:
            return
        self.json_data['members'][member.id] = dict(roles=[x.id for x in member.roles if x.id in self.saved_roles],
                                                    nickname='None' if member.nick is None else member.nick,
                                                    name=member.display_name)
        with open('roles.json','w') as json_file:
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

    @commands.group()
    async def roleKeep(self):
        """The commands group for adding and removing roles to be kept on sever join/leave"""
        pass

    @roleKeep.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def add(self, ctx, *, roleName:str):
        """The command to add roles to the sticky role list"""
        role = discord.utils.get(ctx.message.server.roles, name=roleName)
        if role is not None:
            if role.id not in self.saved_roles:
                self.json_data['saving_roles'].append(role.id)
                self.saved_roles = self.json_data["saving_roles"]
                with open('roles.json', 'w') as json_file:
                    json_file.write(json.dumps(self.json_data, indent=2))
                await self.bot.say('Added {} to the list of sticky roles!'.format(roleName))
            else:
                await self.bot.say('{} is already sticky!'.format(roleName))
        else:
            await self.bot.say('Unabled to find a role by that name!')

    @roleKeep.command(pass_context=True)
    @mod_or_permissions(manage_roles=True)
    async def remove(self, ctx, *, roleName:str):
        """The command to remove roles from the sticky role list"""
        role = discord.utils.get(ctx.message.server.roles, name=roleName)
        if role is not None:
            if role.id in self.saved_roles:
                self.json_data['saving_roles'].remove(role.id)
                self.saved_roles = self.json_data['saving_roles']
                with open('roles.json', 'w') as json_file:
                    json_file.write(json.dumps(self.json_data, indent=2))
                await self.bot.say('Removed {} from the list of sticky roles!'.format(roleName))
            else:
                await self.bot.say('{} is not a sticky role!'.format(roleName))
        else:
            await self.bot.say('Unabled to find a role by that name!')







def setup(bot):
    bot.add_cog(roleKeeper(bot))
