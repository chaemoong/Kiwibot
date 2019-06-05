"""Warning cog"""

# Credits go to Twentysix26 for modlog
# https://github.com/Twentysix26/Red-DiscordBot/blob/develop/cogs/mod.py
#bot.change_nickname(user, display_name + "💩")
import discord
import os
import shutil
import aiohttp
import asyncio

from .utils.chat_formatting import *
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from discord.ext import commands
from enum import Enum
from collections import deque, defaultdict, OrderedDict
from __main__ import send_cmd_help, settings

default_settings = {
    "ban_mention_spam"  : False,
    "delete_repeats"    : False,
    "mod-log"           : True,
    "respect_hierarchy" : False
}


default_warn = ("user.mention님께서 경고 1회를 받으셨습니다. \n"
                "warn.count/warn.limit \n"
                "경고 warn.limit회가 누적되면 벤을 맞이하게 될것입니다!")
default_max = 10
default_ban = ("그는 경고 warn.limit개가 되었으므로, user.name는 벤 되었습니다!")
class ModError(Exception):
    pass

class NoModLogChannel(ModError):
    pass

class Warn:
    def __init__(self, bot):
        self.bot = bot
        self.profile = "data/account/warnings.json"
        self.riceCog = dataIO.load_json(self.profile)
        settings = dataIO.load_json("data/mod/settings.json")
        self.settings = defaultdict(lambda: default_settings.copy(), settings)
        self.cases = dataIO.load_json("data/mod/settings.json")
        self.warning_settings = "data/account/warning_settings.json"
        self.riceCog2 = dataIO.load_json(self.warning_settings)
        self.global_ignores = dataIO.load_json("data/account/warning_reason.json")
        settings = dataIO.load_json("data/mod/settings.json")
        if not self.bot.get_cog("Mod"):
            print("You need the Mod cog to run this cog effectively!")
        

    @commands.group(no_pm=True, pass_context=True, name='warnset')
    async def _warnset(self, ctx):
        if ctx.message.server.id not in self.riceCog2:
            self.riceCog2[ctx.message.server.id] = {}
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            server = ctx.message.server
            try:
                msg = self.riceCog2[server.id]["warn_message"]
            except:
                msg = default_warn
            try:
                ban = self.riceCog2[server.id]["ban_message"]
            except:
                ban = default_ban
            try:
                _max = self.riceCog2[server.id]["max"]
            except:
                _max = default_max
            message = "```\n"
            message += "Warn Message - {}\n"
            message += "ban Message - {}\n"
            message += "Warn Limit   - {}\n"
            message += "```"
            await self.bot.say(message.format(msg,
                                              ban,
                                              _max))

    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def pm(self, ctx):
        """Enable/disable PM warn"""
        server = ctx.message.server
        if 'pm_warn' not in self.riceCog[server.id]:
            self.riceCog[server.id]['pm_warn'] = False

        p = self.riceCog[server.id]['pm_warn']
        if p:
            self.riceCog[server.id]['pm_warn'] = False
            await self.bot.say("Warnings are now in the channel.")
        elif not p:
            self.riceCog[server.id]['pm_warn'] = True
            await self.bot.say("Warnings are now in DM.")

    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def poop(self, ctx):
        """Enable/disable poop emojis per warning."""
        server = ctx.message.server
        true_msg = "Poop emojis per warning enabled."
        false_msg = "Poop emojis per warning disabled."
        if 'poop' not in self.riceCog2[server.id]:
            self.riceCog2[server.id]['poop'] = True
            msg = true_msg
        elif self.riceCog2[server.id]['poop'] == True:
            self.riceCog2[server.id]['poop'] = False
            msg = false_msg
        elif self.riceCog2[server.id]['poop'] == False:
            self.riceCog2[server.id]['poop'] = True
            msg = true_msg
        else:
            msg = "Error."
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say(msg)

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def max(self, ctx, limit: int):
        server = ctx.message.server

        self.riceCog2[server.id]["max"] = limit
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Warn limit is now: \n{}".format(limit))

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def ban(self, ctx, *, msg=None):
        """Set the ban message.
        To get a full list of information, use **warnset message** without any parameters."""
        if not msg:
            await self.bot.say("```Set the ban message.\n\n"
                               "To get a full list of information, use "
                               "**warnset message** without any parameters.```")
            return
        server = ctx.message.server

        self.riceCog2[server.id]["ban_message"] = msg
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("ban message is now: \n{}".format(msg))

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def reset(self, ctx):
        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel
        await self.bot.say("Are you sure you want to reset all warn settings"
                           "for this server?\n"
                           "Type **yes** within the next 15 seconds.")
        msg = await self.bot.wait_for_message(author=author,
                                              channel=channel,
                                              timeout=15.0)
        if msg.content.lower().strip() == "yes":
            self.riceCog2[server.id]["warn_message"] = default_warn
            self.riceCog2[server.id]["ban_message"] = default_ban
            self.riceCog2[server.id]["max"] = default_max
        else:
            await self.bot.say("Nevermind then.")
            return

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def message(self, ctx, *, msg=None):
        """Set the warning message
        user.mention - mentions the user
        user.name   - names the user
        user.id     - gets id of user
        warn.count  - gets the # of this warn
        warn.limit  - # of warns allowed
        Example:
        **You, user.mention, have received Warning warn.count. After warn.limit,
        you will be baned.**
        You can set it either for every server.
        To set the ban message, use *warnset ban*
        """
        if not msg:
            await self.bot.say("```Set the warning message\n\n"
                               "user.mention - mentions the user\n"
                               "user.name   - names the user\n"
                               "user.id     - gets id of user\n"
                               "warn.count  - gets the # of this warn\n"
                               "warn.limit  - # of warns allowed\n\n"

                               "Example:\n\n"

                               "**You, user.mention, have received Warning "
                               "warn.count. After warn.limit, you will be "
                               "baned.**\n\n"

                               "You can set it either for every server.\n"
                               "To set the ban message, use *warnset ban*\n```")
            return

        server = ctx.message.server

        self.riceCog2[server.id]["warn_message"] = msg
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Warn message is now: \n{}".format(msg))

    async def filter_message(self, msg, user, count, _max):
        msg = msg.replace("user.mention",
                          user.mention)
        msg = msg.replace("user.name",
                          user.name)
        msg = msg.replace("user.id",
                          user.id)
        msg = msg.replace("warn.count",
                          str(count))
        msg = msg.replace("warn.limit",
                          str(_max))
        return msg


    async def hierarchy(self, ctx):
        """Toggles role hierarchy check for mods / admins"""
        server = ctx.message.server
        toggled = self.settings[server.id].get("respect_hierarchy",
                                               default_settings["respect_hierarchy"])
        if not toggled:
            self.settings[server.id]["respect_hierarchy"] = True
            await self.bot.say("Role hierarchy will be checked when "
                               "moderation commands are issued.")
        else:
            self.settings[server.id]["respect_hierarchy"] = False
            await self.bot.say("Role hierarchy will be ignored when "
                               "moderation commands are issued.")
        dataIO.save_json("data/mod/settings.json", self.settings)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def warn(self, ctx, user: discord.Member, *, reason=None):
        """유저에게 경고를 주는 명령어 입니다
        경고 10개 이면 벤을 당하게 됩니다!"""
        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel

        can_role = channel.permissions_for(server.me).manage_roles

        if not self.is_allowed_by_hierarchy(server, author, user):
            await self.bot.say("저는 그럴수 없어요. 당신은 "
                               "그 보다 높지도 않은 역할이 있으면서 경고를 "
                               "주려하네요. 경고 주는 것을 반대합니다!")
            return

        if server.id not in self.riceCog2:
            msg = default_warn
            ban = default_ban
            _max = default_max

        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}

        if 'pm_warn' not in self.riceCog[server.id]:
            self.riceCog[server.id]['pm_warn'] = False

        p = self.riceCog[server.id]['pm_warn']

        try:
            msg = self.riceCog2[server.id]["warn_message"]
        except:
            msg = default_warn
        try:
            ban = self.riceCog2[server.id]["ban_message"]
        except:
            ban = default_ban
        try:
            _max = self.riceCog2[server.id]["max"]
        except:
            _max = default_max

        colour = server.me.colour

        # checks if the user is in the file
        if server.id not in self.riceCog2:
            self.riceCog2[server.id] = {}
            dataIO.save_json(self.warning_settings,
                             self.riceCog2)
        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            dataIO.save_json(self.profile,
                             self.riceCog)
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        else:
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass

        if "Count" in self.riceCog[server.id][user.id]:
            count = self.riceCog[server.id][user.id]["Count"]
        else:
            count = 0

        cog = self.bot.get_cog('Mod')

        # checks how many warnings the user has
        if count != _max - 1:
            count += 1
            msg = await self.filter_message(msg=msg,
                                            user=user,
                                            count=count,
                                            _max=_max)
            data = discord.Embed(colour=colour)
            data.add_field(name="경고",
                           value=msg)
            if reason:
                data.add_field(name="사유",
                               value=reason,
                               inline=False)
            data.set_footer(text=self.bot.user.name)
            if p:
                await self.bot.send_message(user, embed=data)
            elif not p:
                await self.bot.say(embed=data)
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            log = None
        else:
            msg = ban
            msg = await self.filter_message(msg=msg,
                                            user=user,
                                            count=count,
                                            _max=_max)
            data = discord.Embed(colour=colour)
            data.add_field(name="경고",
                           value=msg)
            if reason:
                data.add_field(name="사유",
                               value=reason,
                               inline=False)

            data.set_footer(text=self.bot.user.name)
            if p:
                await self.bot.send_message(user, embed=data)
            elif not p:
                mod_channel = server.get_channel(settings[server.id]["mod-log"])
                await self.bot.send_message(mod_channel, 'test')
                await self.bot.say(embed=data)
            count = 0
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            log = "ban"

        if 'poop' in self.riceCog2[server.id] and can_role:
            if self.riceCog2[server.id]['poop'] == True:
                poops = count * "💩"
                role_name = "Warning {}".format(poops)
                is_there = False
                colour = 0xbc7642
                for role in server.roles:
                    if role.name == role_name:
                        poop_role = role
                        is_there = True
                if not is_there:
                    poop_role = await self.bot.create_role(server)
                    await self.bot.edit_role(role=poop_role,
                                             name=role_name,
                                             server=server)
                try:
                    await self.bot.add_roles(user,
                                             poop_role)
                except discord.errors.Forbidden:
                    await self.bot.say("No permission to add roles")

        if (reason and log):
            await cog.new_case(server=server,
                               action=log,
                               mod=author,
                               user=user,
                               reason=reason)
            await self.bot.ban(user)
        elif log:
            await cog.new_case(server=server,
                               action=log,
                               user=user,
                               mod=author,
                               reason="No reason provided yet.")
            await self.bot.ban(user)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def clean(self, ctx, user: discord.Member):
        author = ctx.message.author
        server = author.server
        colour = server.me.colour

        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            dataIO.save_json(self.profile,
                             self.riceCog)
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        else:
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass

        if "Count" in self.riceCog[server.id][user.id]:
            count = self.riceCog[server.id][user.id]["Count"]
        else:
            count = 0

        if count != 0:
            msg = str(user.mention) + "님의 경고 기록이 초기화 되었습니다!"
            data = discord.Embed(colour=colour)
            data.add_field(name="경고 초기화",
                           value=msg)
            data.set_footer(text=self.bot.user.name)
            await self.bot.say(embed=data)

            count = 0
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
        else:
            await self.bot.say((user.mention) + "님은 경고가 없어요!")
            # clear role

    @commands.command(pass_context=True, no_pm=True)
    async def check(self, ctx, *, user: discord.Member=None):
        author = ctx.message.author
        server = author.server
        colour = server.me.colour

        if not user:
            user = author
        else:
            pass
        try:
            count = self.riceCog[server.id][user.id]["Count"]
            msg = ("<@{}>님의 경고는 {}개 입니다!".format(user.id, count))
            data = discord.Embed(colour=colour)
            data.add_field(name="경고 확인",
                        value=msg)
            data.set_footer(text=self.bot.user.name)
            await self.bot.say(embed=data)
        except KeyError:
            msg1 = ("<@{}>님의 경고는 0개 입니다!".format(user.id))
            check = discord.Embed(colour=colour)
            check.add_field(name='경고 확인', value=msg1)
            check.set_footer(text=self.bot.user.name)
            await self.bot.say(embed=check)



    def is_allowed_by_hierarchy(self, server, mod, user):
        toggled = self.settings[server.id].get("respect_hierarchy",
                                               default_settings["respect_hierarchy"])
        is_special = mod == server.owner or mod.id == self.bot.settings.owner

        if not toggled:
            return True
        else:
            return mod.top_role.position > user.top_role.position or is_special
def check_folder():
    if not os.path.exists("data/account"):
        print("Creating data/account/server.id folder")
        os.makedirs("data/account")


def check_file():
    data = {}
    f = "data/account/warnings.json"
    g = "data/account/warning_settings.json"
    if not dataIO.is_valid_json(f):
        print("data/account/warnings.json 파일을 만드는 중...")
        dataIO.save_json(f,
                         data)
    if not dataIO.is_valid_json(g):
        print("data/account/warning_settings.json 파일을 만드는 중...")
        dataIO.save_json(g,
                         data)



def setup(bot):
    check_folder()
    check_file()
    bot.add_cog(Warn(bot))