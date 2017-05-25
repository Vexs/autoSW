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
        if member.nick is None and len(member.roles == 0):
            return
        elif member.nick is not None:
            self.json_data['members'][member.id] = {
                'roles': [x.id for x in member.roles if x.id in self.saved_roles], 'nickname': member.nick}
        else:
            self.json_data['members'][member.id] = {
                'roles': [x.id for x in member.roles if x.id in self.saved_roles], 'nickname': 'None'}
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




def setup(bot):
    bot.add_cog(roleKeeper(bot))
