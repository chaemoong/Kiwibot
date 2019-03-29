from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from .utils.chat_formatting import pagify, box
import discord
import os
import re


class CustomCommands:
    """커스텀 명령어 설정 명령어입니다!

    Creates commands used to display text"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/customcom/commands.json"
        self.c_commands = dataIO.load_json(self.file_path)

    @commands.group(aliases=["cc"], pass_context=True, no_pm=True)
    async def customcom(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @customcom.command(name="add", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def cc_add(self, ctx, command : str, *, text):
        """커스텀 명령어를 추가합니다

        예:
        !!cc add <명령어> <원하는 멘트>
        """
        server = ctx.message.server
        command = command.lower()
        if command in self.bot.commands:
            embed = discord.Embed(
                title='잠시만요!'
            )
            embed.add_field(name='그 명령어는 봇 명령어에 존재합니다!', value='그 명령어 말고 다른 멘트로 해주시기 바랍니다!')
            await self.bot.say(embed=embed)
            return
        if server.id not in self.c_commands:
            self.c_commands[server.id] = {}
        cmdlist = self.c_commands[server.id]
        if command not in cmdlist:
            cmdlist[command] = text
            self.c_commands[server.id] = cmdlist
            dataIO.save_json(self.file_path, self.c_commands)
            await self.bot.say("커스텀 커맨드가 추가 되었습니다!")
        else:
            await self.bot.say("그 명령어는 존재하는 커스텀명령어 입니다!"
                               "`{}customcom edit`을 사용하여 그 명령어를 "
                               "수정하십시오!".format(ctx.prefix))

    @customcom.command(name="edit", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def cc_edit(self, ctx, command : str, *, text):
        """커스텀 커맨드를 수정합니다!

        예:
        !!cc edit 커맨드 <원하는 멘트>
        """
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist[command] = text
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("커스텀커맨드가 성공적으로 수정 되었습니다")
            else:
                await self.bot.say("그 명령어는 존재하시 않습니다! "
                                   "`{}customcom add`을 이용하여 커스텀명령어를 추가하십시오!"
                                   "".format(ctx.prefix))
        else:
            await self.bot.say("그 커스텀 커맨드는 이 서버의 커스텀 커맨드가 아닙니다!"
                               "`{}customcom add`을 사용하여 커스텀 커맨드를 추가하십니오."
                               "".format(ctx.prefix))

    @customcom.command(name="delete", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def cc_delete(self, ctx, command : str):
        """커스텀 커맨드를 삭제하는 명령어 입니다!
        예 :
        
        !!cc delete 원하는 커맨드
            """
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist.pop(command, None)
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("커스텀커맨드가 성공적으로 삭제 되었습니다!")
            else:
                await self.bot.say("그 커스텀 커맨드는 존재하지 않습니다!")
        else:
            await self.bot.say("그 커스텀 커맨드는 이 서버의 커맨드가 아닙니다!"
                               " `{}customcom add` 을 사용하여 추가 하시기 바랍니다!"
                               "".format(ctx.prefix))

    @customcom.command(name="list", pass_context=True)
    async def cc_list(self, ctx):
        """커스텀 커맨드 목록을 나타냅니다!"""
        server = ctx.message.server
        commands = self.c_commands.get(server.id, {})

        if not commands:
            await self.bot.say("그 커스텀 커맨드는 이 서버의 커맨드가 아닙니다!"
                               " `{}customcom add` 을 사용하여 추가 하시기 바랍니다!"
                               "".format(ctx.prefix))
            return

        commands = ", ".join([ctx.prefix + c for c in sorted(commands)])
        commands = "커스텀 명령어들:\n\n" + commands

        if len(commands) < 1500:
            await self.bot.say(box(commands))
        else:
            for page in pagify(commands, delims=[" ", "\n"]):
                await self.bot.whisper(box(page))

    async def on_message(self, message):
        if len(message.content) < 2 or message.channel.is_private:
            return

        server = message.server
        prefix = self.get_prefix(message)

        if not prefix:
            return

        if server.id in self.c_commands and self.bot.user_allowed(message):
            cmdlist = self.c_commands[server.id]
            cmd = message.content[len(prefix):]
            if cmd in cmdlist:
                cmd = cmdlist[cmd]
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)
            elif cmd.lower() in cmdlist:
                cmd = cmdlist[cmd.lower()]
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)

    def get_prefix(self, message):
        for p in self.bot.settings.get_prefixes(message.server):
            if message.content.startswith(p):
                return p
        return False

    def format_cc(self, command, message):
        results = re.findall("\{([^}]+)\}", command)
        for result in results:
            param = self.transform_parameter(result, message)
            command = command.replace("{" + result + "}", param)
        return command

    def transform_parameter(self, result, message):
        """
        For security reasons only specific objects are allowed
        Internals are ignored
        """
        raw_result = "{" + result + "}"
        objects = {
            "message" : message,
            "author"  : message.author,
            "channel" : message.channel,
            "server"  : message.server
        }
        if result in objects:
            return str(objects[result])
        try:
            first, second = result.split(".")
        except ValueError:
            return raw_result
        if first in objects and not second.startswith("_"):
            first = objects[first]
        else:
            return raw_result
        return str(getattr(first, second, raw_result))


def check_folders():
    if not os.path.exists("data/customcom"):
        print("Creating data/customcom folder...")
        os.makedirs("data/customcom")


def check_files():
    f = "data/customcom/commands.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty commands.json...")
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(CustomCommands(bot))
