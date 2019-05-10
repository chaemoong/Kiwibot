import discord
from discord.ext import commands
from cogs.utils import checks
from cogs.utils.converters import GlobalUser
from __main__ import set_cog
from .utils.dataIO import dataIO
from .utils.chat_formatting import pagify, box
from asyncio.subprocess import PIPE
from .utils.chat_formatting import pagify
from subprocess import Popen
from discord.ext import commands


import importlib
import traceback
import logging
import asyncio
import threading
import datetime
import glob
import os
import aiohttp

log = logging.getLogger("red.owner")



class CogNotFoundError(Exception):
    pass


class CogLoadError(Exception):
    pass


class NoSetupError(CogLoadError):
    pass


class CogUnloadError(Exception):
    pass


class OwnerUnloadWithoutReloadError(CogUnloadError):
    pass


class Owner:
    """All owner-only commands that relate to debug bot operations."""

    def __init__(self, bot):
        self.bot = bot
        self.setowner_lock = False
        self.disabled_commands = dataIO.load_json("data/red/disabled_commands.json")
        self.global_ignores = dataIO.load_json("data/red/global_ignores.json")
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    @checks.is_owner()
    async def load(self, *, cog_name: str):
        """기능을 불러옵니다!
        
        예시: k!load mod"""
        module = cog_name.strip()
        if "cogs." not in module:
            module = "cogs." + module
        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("그 기능은 존재 하지 않는 기능입니다")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("그 기능을 불러오는 도중 에러가 발생하였습니다!\n콘솔 혹은 터미널을 확인해주세요!")
        except Exception as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("그 기능을 불러오는 도중 에러가 발생하였습니다!\n콘솔 혹은 터미널을 확인해주세요!")
        else:
            set_cog(module, True)
            await self.disable_commands()
            await self.bot.say("기능이 추가 되었습니다!")

    @commands.group(invoke_without_command=True)
    @checks.is_owner()
    async def unload(self, *, cog_name: str):
        """기능을 비활성화 합니다!

        예시: unload mod"""
        module = cog_name.strip()
        if "cogs." not in module:
            module = "cogs." + module
        if not self._does_cogfile_exist(module):
            await self.bot.say("그 기능을 찾을 수 없습니다!")
        else:
            set_cog(module, False)
        try:  # No matter what we should try to unload it
            self._unload_cog(module)
        except OwnerUnloadWithoutReloadError:
            await self.bot.say("오너 기능은 비활성화 할 수 없습니다!")
        except CogUnloadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say('비활성화 도중 에러가 발생했습니다!')
        else:
            await self.bot.say("그 기능은 사용 불가 입니다!")

    @unload.command(name="all")
    @checks.is_owner()
    async def unload_all(self):
        """모든 기능을 비활성화 합니다!"""
        cogs = self._list_cogs()
        still_loaded = []
        for cog in cogs:
            set_cog(cog, False)
            try:
                self._unload_cog(cog)
            except OwnerUnloadWithoutReloadError:
                pass
            except CogUnloadError as e:
                log.exception(e)
                traceback.print_exc()
                still_loaded.append(cog)
        if still_loaded:
            still_loaded = ", ".join(still_loaded)
            await self.bot.say("I was unable to unload some cogs: "
                "{}".format(still_loaded))
        else:
            await self.bot.say("All cogs are now unloaded.")

    @checks.is_owner()
    @commands.command(name="reload")
    async def _reload(self, *, cog_name: str):
        """기능을 리로드 합니다!

        예시: reload audio"""
        module = cog_name.strip()
        if "cogs." not in module:
            module = "cogs." + module

        try:
            self._unload_cog(module, reloading=True)
        except:
            pass

        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("그 기능을 찾을 수 없습니다.")
        except NoSetupError:
            await self.bot.say("그 기능은 먼저 설치를 하셔아 합니다.")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("그 기능을 로드중 오류가 발생했습니다."
                               " 콘솔 혹은 터미널을 확인해주세요.")
        else:
            set_cog(module, True)
            await self.disable_commands()
            await self.bot.say("이 기능은 리로드되었습니다.")

    @commands.command(name="cogs")
    @checks.is_owner()
    async def _show_cogs(self):
        """Shows loaded/unloaded cogs"""
        # This function assumes that all cogs are in the cogs folder,
        # which is currently true.

        # Extracting filename from __module__ Example: cogs.owner
        loaded = [c.__module__.split(".")[1] for c in self.bot.cogs.values()]
        # What's in the folder but not loaded is unloaded
        unloaded = [c.split(".")[1] for c in self._list_cogs()
                    if c.split(".")[1] not in loaded]

        if not unloaded:
            unloaded = ["None"]

        msg = ("+ 로드됨\n"
               "{}\n\n"
               "- 언로드됨\n"
               "{}"
               "".format(", ".join(sorted(loaded)),
                         ", ".join(sorted(unloaded)))
               )
        for page in pagify(msg, [" "], shorten_by=16):
            await self.bot.say(box(page.lstrip(" "), lang="diff"))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def rules(self, ctx):
        """팀멜론 규칙 (사용금지)"""
        em = discord.Embed(colour=discord.Colour.green(), title='팀 멜론 서포트 규칙')
        em.add_field(name='아래의 규칙을 어길시 벤 처리 합니다', value='```diff\n- 이 서버의 인원에게 부모님 욕(일명 패드립), 성희롱, 비하발언을 사용하면 안됩니다!\n+ DM(PM)으로 하시는건 더더욱 안됩니다!\n- 바이러스 파일 업로드 금지.\n- 프로필사진이 음란물이 관련되어있으면 변경을 해주시기 바랍니다.```')
        em.add_field(name='이 아래에 있는 모든 규칙들은 경고로 처리됩니다!', value='```fix\n> 타인에게 욕을 하시면 안됩니다!\n> 도배 금지(예시: 따로 사진으로 업로드 됩니다)\n> 단타도배(예시: 따로 사진으로 업로드 됩니다!)\n> 홍보는 전면 금지입니다[디스코드 서버는 모두 처벌, 유튜브 링크는 관리자가 보이게 괜찮다고 생각하면 상관 X]\n>분쟁 유도는 금지입니다! [가벼운 분쟁이면 경고 조치하지만 심하게 갈 경우 벤 조치 하도록 하겠습니다]\n```')
        em.add_field(name='이모지 및 반응 추가 규칙', value='```diff\n+ 욕 이모지 금지\n+ 음란물을 표현하는 이모지 추가 금지\n+ 이모지 도배 금지```[예시 : :thinking: :thinking: :thinking: :thinking: :thinking: :thinking: :thinking: :thinking:]')
        em.add_field(name='음성 채팅방 규칙', value='음성 채널이여도 욕설은 금지 됩니다! [증거 없을시 처벌안됩니다!]\n소음을 유발하는 행위는 금지합니다!\n<@184405311681986560> 봇 사용금지')
        em.add_field(name='관리자 신고', value='일반 유저가 아닌 관리자가 규칙을 어겼을시 <@417123204469882890>으로 DM(PM) 부탁드립니다!')
        em.set_footer(text='도리닭 님의 규칙을 사용하였음을 알려드립니다!')
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def cmd(self, ctx, *, code=None):
        """코드 쑤셔 박기(?)"""
        def check(m):
            if m.content.strip().lower() == "more":
                return True

        author = ctx.message.author
        channel = ctx.message.channel

        code = code.strip('` ')
        result = None

        global_vars = globals().copy()
        global_vars['bot'] = self.bot
        global_vars['ctx'] = ctx
        global_vars['message'] = ctx.message
        global_vars['author'] = ctx.message.author
        global_vars['channel'] = ctx.message.channel
        global_vars['server'] = ctx.message.server

        try:
            result = eval(code, global_vars, locals())
        except Exception as e:
            await self.bot.say(box('{}: {}'.format(type(e).__name__, str(e)),
                                   lang="py"))
            return

        if asyncio.iscoroutine(result):
            result = await result

        result = str(result)

        if not ctx.message.channel.is_private:
            censor = (self.bot.settings.email,
                      self.bot.settings.password,
                      self.bot.settings.token)
            r = "[EXPUNGED]"
            for w in censor:
                if w is None or w == "":
                    continue
                result = result.replace(w, r)
                result = result.replace(w.lower(), r)
                result = result.replace(w.upper(), r)

        result = list(pagify(result, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - (i+1)))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      check=check,
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    @commands.group(name="set", pass_context=True)
    async def _set(self, ctx):
        """키위봇을 설정하는 명령어입니다!"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def owner(self, ctx):
        """주인 설정"""
        if self.bot.settings.no_prompt is True:
            await self.bot.say("Console interaction is disabled. Start Red "
                               "without the `--no-prompt` flag to use this "
                               "command.")
            return
        if self.setowner_lock:
            await self.bot.say("이 명령어는 잠겨져 있습니다!")
            return

        if self.bot.settings.owner is not None:
            await self.bot.say(
            "The owner is already set. Remember that setting the owner "
            "to someone else other than who hosts the bot has security "
            "repercussions and is *NOT recommended*. Proceed at your own risk."
            )
            await asyncio.sleep(3)

        await self.bot.say("Confirm in the console that you're the owner.")
        self.setowner_lock = True
        t = threading.Thread(target=self._wait_for_answer,
                             args=(ctx.message.author,))
        t.start()

    @_set.command()
    @checks.is_owner()
    async def defaultmodrole(self, *, role_name: str):
        """Sets the default mod role name

           This is used if a server-specific role is not set"""
        self.bot.settings.default_mod = role_name
        self.bot.settings.save_settings()
        await self.bot.say("The default mod role name has been set.")

    @_set.command()
    @checks.is_owner()
    async def defaultadminrole(self, *, role_name: str):
        """Sets the default admin role name

           This is used if a server-specific role is not set"""
        self.bot.settings.default_admin = role_name
        self.bot.settings.save_settings()
        await self.bot.say("The default admin role name has been set.")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def prefix(self, ctx, *prefixes):
        """grand kiwi bot의 접두사를 수정합니다!

        Accepts multiple prefixes separated by a space. Enclose in double
        quotes if a prefix contains spaces.
        Example: set prefix ! $ ? "two words" """
        if prefixes == ():
            await self.bot.send_cmd_help(ctx)
            return

        self.bot.settings.prefixes = sorted(prefixes, reverse=True)
        self.bot.settings.save_settings()
        log.debug("Setting global prefixes to:\n\t{}"
                  "".format(self.bot.settings.prefixes))

        p = "prefixes" if len(prefixes) > 1 else "prefix"
        await self.bot.say("Global {} set".format(p))

    @_set.command(pass_context=True, no_pm=True)
    @checks.serverowner_or_permissions(administrator=True)
    async def serverprefix(self, ctx, *prefixes):
        """Sets Red's prefixes for this server

        Accepts multiple prefixes separated by a space. Enclose in double
        quotes if a prefix contains spaces.
        Example: set serverprefix ! $ ? "two words"

        Issuing this command with no parameters will reset the server
        prefixes and the global ones will be used instead."""
        server = ctx.message.server

        if prefixes == ():
            self.bot.settings.set_server_prefixes(server, [])
            self.bot.settings.save_settings()
            current_p = ", ".join(self.bot.settings.prefixes)
            await self.bot.say("Server prefixes reset. Current prefixes: "
                               "`{}`".format(current_p))
            return

        prefixes = sorted(prefixes, reverse=True)
        self.bot.settings.set_server_prefixes(server, prefixes)
        self.bot.settings.save_settings()
        log.debug("Setting server's {} prefixes to:\n\t{}"
                  "".format(server.id, self.bot.settings.prefixes))

        p = "Prefixes" if len(prefixes) > 1 else "Prefix"
        await self.bot.say("{} set for this server.\n"
                           "To go back to the global prefixes, do"
                           " `{}set serverprefix` "
                           "".format(p, prefixes[0]))

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def name(self, ctx, *, name):
        """grand kiwi bot 이름 설정"""
        name = name.strip()
        if name != "":
            try:
                await self.bot.edit_profile(self.bot.settings.password,
                                            username=name)
            except:
                await self.bot.say("Failed to change name. Remember that you"
                                   " can only do it up to 2 times an hour."
                                   "Use nicknames if you need frequent "
                                   "changes. {}set nickname"
                                   "".format(ctx.prefix))
            else:
                await self.bot.say("완료.")
        else:
            await self.bot.send_cmd_help(ctx)

    @_set.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def nickname(self, ctx, *, nickname=""):
        """별명 설정

        Leaving this empty will remove it."""
        nickname = nickname.strip()
        if nickname == "":
            nickname = None
        try:
            await self.bot.change_nickname(ctx.message.server.me, nickname)
            await self.bot.say("완료.")
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Change Nickname\" permission.")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def game(self, ctx, *, game=None):
        """플레이중 설정

        Leaving this empty will clear it."""

        server = ctx.message.server

        current_status = server.me.status if server is not None else None

        if game:
            game = game.strip()
            await self.bot.change_presence(game=discord.Game(name=game),
                                           status=current_status)
            log.debug('Status set to "{}" by owner'.format(game))
        else:
            await self.bot.change_presence(game=None, status=current_status)
            log.debug('status cleared by owner')
        await self.bot.say("완료.")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def status(self, ctx, *, status=None):
        """상태 설정

        상태들:
            online
            idle
            dnd
            invisible"""

        statuses = {
                    "online"    : discord.Status.online,
                    "idle"      : discord.Status.idle,
                    "dnd"       : discord.Status.dnd,
                    "invisible" : discord.Status.invisible
                   }

        server = ctx.message.server

        current_game = server.me.game if server is not None else None

        if status is None:
            await self.bot.change_presence(status=discord.Status.online,
                                           game=current_game)
            await self.bot.say("상태가 초기화 되었습니다.")
        else:
            status = statuses.get(status.lower(), None)
            if status:
                await self.bot.change_presence(status=status,
                                               game=current_game)
                await self.bot.say("상태가 바뀌었습니다.")
            else:
                await self.bot.send_cmd_help(ctx)

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def stream(self, ctx, streamer=None, *, stream_title=None):
        """Sets Red's streaming status

        Leaving both streamer and stream_title empty will clear it."""

        server = ctx.message.server

        current_status = server.me.status if server is not None else None

        if stream_title:
            stream_title = stream_title.strip()
            if "twitch.tv/" not in streamer:
                streamer = "https://www.twitch.tv/" + streamer
            game = discord.Game(type=1, url=streamer, name=stream_title)
            await self.bot.change_presence(game=game, status=current_status)
            log.debug('Owner has set streaming status and url to "{}" and {}'.format(stream_title, streamer))
        elif streamer is not None:
            await self.bot.send_cmd_help(ctx)
            return
        else:
            await self.bot.change_presence(game=None, status=current_status)
            log.debug('stream cleared by owner')
        await self.bot.say("완료.")

    @_set.command()
    @checks.is_owner()
    async def avatar(self, url):
        """grand kiwi bot의 아바타 설정"""
        try:
            async with self.session.get(url) as r:
                data = await r.read()
            await self.bot.edit_profile(self.bot.settings.password, avatar=data)
            await self.bot.say("완료.")
            log.debug("changed avatar")
        except Exception as e:
            await self.bot.say("Error, check your console or logs for "
                               "more information.")
            log.exception(e)
            traceback.print_exc()

    @_set.command(name="token")
    @checks.is_owner()
    async def _token(self, token):
        """이 토큰으로 로그인 하기"""
        if len(token) < 50:
            await self.bot.say("없는 토큰입니다. ~~난데모나이~~")
        else:
            self.bot.settings.token = token
            self.bot.settings.save_settings()
            await self.bot.say("토~~우웩~~큰이 설정 되었습니다. 저를 재시작 하겠습니다.")
            log.debug("Token changed.")

    @_set.command(name="adminrole", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def _server_adminrole(self, ctx, *, role: discord.Role):
        """어드민 역할을 설정 합니다"""
        server = ctx.message.server
        if server.id not in self.bot.settings.servers:
            await self.bot.say("Remember to set modrole too.")
        self.bot.settings.set_server_admin(server, role.name)
        await self.bot.say("어드민 권한이 '{}'으로 설정 되었습니다!".format(role.name))

    @_set.command(name="modrole", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def _server_modrole(self, ctx, *, role: discord.Role):
        """부관리자의 역할을 설정합니다"""
        server = ctx.message.server
        if server.id not in self.bot.settings.servers:
            await self.bot.say("Remember to set adminrole too.")
        self.bot.settings.set_server_mod(server, role.name)
        await self.bot.say("부관리자 역할이 '{}'으로 설정 되었습니다!".format(role.name))

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def blacklist(self, ctx):
        """Blacklist management commands

        Blacklisted users will be unable to issue commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @blacklist.command(name="add")
    async def _blacklist_add(self, user: GlobalUser):
        """유저를 grand kiwi bot 블랙리스트 명단에 추가 시킵니다"""
        if user.id not in self.global_ignores["blacklist"]:
            self.global_ignores["blacklist"].append(user.id)
            self.save_global_ignores()
            await self.bot.say("그 유저는 블랙리스트 명단에 추가되었습니다.")
        else:
            await self.bot.say("그 유저는 이미 명단에 있습니다.")

    @blacklist.command(name="remove")
    async def _blacklist_remove(self, user: GlobalUser):
        """유저를 grand kiwi bot 블랙리스트 명단에 제거 시킵니다"""
        if user.id in self.global_ignores["blacklist"]:
            self.global_ignores["blacklist"].remove(user.id)
            self.save_global_ignores()
            await self.bot.say("그 유저는 블랙리스트 명단에서 컷 당하였습니다!")
        else:
            await self.bot.say("그 유저는 블랙리스트 명단에 없습니다!.")

    @blacklist.command(name="list")
    async def _blacklist_list(self):
        """Lists users on the blacklist"""
        blacklist = self._populate_list(self.global_ignores["blacklist"])

        if blacklist:
            for page in blacklist:
                await self.bot.say(box(page))
        else:
            await self.bot.say("블랙리스트 명단이 비어있습니다!")

    @blacklist.command(name="clear")
    async def _blacklist_clear(self):
        """블랙리스트 명단을 비웁니다!"""
        self.global_ignores["blacklist"] = []
        self.save_global_ignores()
        await self.bot.say("명단이 이제 비었습니다!.")

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def whitelist(self, ctx):
        """Whitelist management commands

        If the whitelist is not empty, only whitelisted users will
        be able to use Red"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @whitelist.command(name="add")
    async def _whitelist_add(self, user: GlobalUser):
        """Adds user to Red's global whitelist"""
        if user.id not in self.global_ignores["whitelist"]:
            if not self.global_ignores["whitelist"]:
                msg = "\nNon-whitelisted users will be ignored."
            else:
                msg = ""
            self.global_ignores["whitelist"].append(user.id)
            self.save_global_ignores()
            await self.bot.say("User has been whitelisted." + msg)
        else:
            await self.bot.say("User is already whitelisted.")

    @whitelist.command(name="remove")
    async def _whitelist_remove(self, user: GlobalUser):
        """Removes user from Red's global whitelist"""
        if user.id in self.global_ignores["whitelist"]:
            self.global_ignores["whitelist"].remove(user.id)
            self.save_global_ignores()
            await self.bot.say("User has been removed from the whitelist.")
        else:
            await self.bot.say("User is not whitelisted.")

    @whitelist.command(name="list")
    async def _whitelist_list(self):
        """Lists users on the whitelist"""
        whitelist = self._populate_list(self.global_ignores["whitelist"])

        if whitelist:
            for page in whitelist:
                await self.bot.say(box(page))
        else:
            await self.bot.say("The whitelist is empty.")

    @whitelist.command(name="clear")
    async def _whitelist_clear(self):
        """Clears the global whitelist"""
        self.global_ignores["whitelist"] = []
        self.save_global_ignores()
        await self.bot.say("Whitelist is now empty.")

    @commands.command()
    @checks.is_owner()
    async def shutdown(self, silently : bool=False):
        """grand kiwi bot 종료 커맨드"""
        wave = "\N{WAVING HAND SIGN}"
        skin = "\N{EMOJI MODIFIER FITZPATRICK TYPE-3}"
        try: # We don't want missing perms to stop our shutdown
            if not silently:
                await self.bot.say("꺼지는중... " + wave + skin)
        except:
            pass
        await self.bot.shutdown()

    @commands.command()
    @checks.is_owner()
    async def restart(self, silently : bool=False):
        try:
            if not silently:
                await self.bot.say("재시작중...")
        except:
            pass
        await self.bot.shutdown(restart=True)

    @commands.group(name="command", pass_context=True)
    @checks.is_owner()
    async def command_disabler(self, ctx):
        """해제/동작 명령어들

        이것은 해제된 명령어들 명단입니다"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            if self.disabled_commands:
                msg = "해제된 명령어들:\n```xl\n"
                for cmd in self.disabled_commands:
                    msg += "{}, ".format(cmd)
                msg = msg.strip(", ")
                await self.bot.whisper("{}```".format(msg))

    @command_disabler.command()
    async def disable(self, *, command):
        """Disables commands/subcommands"""
        comm_obj = await self.get_command(command)
        if comm_obj is KeyError:
            await self.bot.say("That command doesn't seem to exist.")
        elif comm_obj is False:
            await self.bot.say("You cannot disable owner restricted commands.")
        else:
            comm_obj.enabled = False
            comm_obj.hidden = True
            self.disabled_commands.append(command)
            self.save_disabled_commands()
            await self.bot.say("그 커맨드는 이제 사용 불가입니다!")

    @command_disabler.command()
    async def enable(self, *, command):
        """Enables commands/subcommands"""
        if command in self.disabled_commands:
            self.disabled_commands.remove(command)
            self.save_disabled_commands()
            await self.bot.say("그 기능은 사용 가능 상태 입니다!")
        else:
            await self.bot.say("그 기능은 사용 가능 상태 입니다!")
            return
        try:
            comm_obj = await self.get_command(command)
            comm_obj.enabled = True
            comm_obj.hidden = False
        except:  # In case it was in the disabled list but not currently loaded
            pass # No point in even checking what returns

    async def get_command(self, command):
        command = command.split()
        try:
            comm_obj = self.bot.commands[command[0]]
            if len(command) > 1:
                command.pop(0)
                for cmd in command:
                    comm_obj = comm_obj.commands[cmd]
        except KeyError:
            return KeyError
        for check in comm_obj.checks:
            if hasattr(check, "__name__") and check.__name__ == "is_owner_check":
                return False
        return comm_obj

    async def disable_commands(self): # runs at boot
        for cmd in self.disabled_commands:
            cmd_obj = await self.get_command(cmd)
            try:
                cmd_obj.enabled = False
                cmd_obj.hidden = True
            except:
                pass
                
    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def leave(self, ctx):
        """서버 나가기"""
        message = ctx.message

        await self.bot.say("당신은 제가 이 서버를 나가는것을 동의 하십니까?"
                           " 그럼 **yes** 를 쓰세요.")
        response = await self.bot.wait_for_message(author=message.author)

        if response.content.lower().strip() == "yes":
            await self.bot.say("ㅇㅋ. Bye :wave:")
            log.debug('Leaving "{}"'.format(message.server.name))
            await self.bot.leave_server(message.server)
        else:
            await self.bot.say("알겠어. 그냥 여기에 뻗어있을게")

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def servers(self, ctx):
        """Lists and allows to leave servers"""
        owner = ctx.message.author
        servers = sorted(list(self.bot.servers),
                         key=lambda s: s.name.lower())
        msg = ""
        for i, server in enumerate(servers):
            msg += "{}: {}\n".format(i, server.name)
        msg += "\nTo leave a server just type its number."

        for page in pagify(msg, ['\n']):
            await self.bot.say(page)

        while msg is not None:
            msg = await self.bot.wait_for_message(author=owner, timeout=15)
            try:
                msg = int(msg.content)
                await self.leave_confirmation(servers[msg], owner, ctx)
                break
            except (IndexError, ValueError, AttributeError):
                pass

    async def leave_confirmation(self, server, owner, ctx):
        await self.bot.say("Are you sure you want me "
                    "to leave {}? (yes/no)".format(server.name))

        msg = await self.bot.wait_for_message(author=owner, timeout=15)

        if msg is None:
            await self.bot.say("I guess not.")
        elif msg.content.lower().strip() in ("yes", "y"):
            await self.bot.leave_server(server)
            if server != ctx.message.server:
                await self.bot.say("완료.")
        else:
            await self.bot.say("Alright then.")

    @commands.command(pass_context=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def contact(self, ctx, *, message : str):
        """주인에게 메시지 보내는것"""
        if self.bot.settings.owner is None:
            await self.bot.say("주인 설정이 안되있음.")
            return
        server = ctx.message.server
        owner = discord.utils.get(self.bot.get_all_members(),
                                  id=self.bot.settings.owner)
        author = ctx.message.author
        footer = "User ID: " + author.id

        if ctx.message.server is None:
            source = "through DM"
        else:
            source = "from {}".format(server)
            footer += " | Server ID: " + server.id

        if isinstance(author, discord.Member):
            colour = author.colour
        else:
            colour = discord.Colour.red()

        description = "Sent by {} {}".format(author, source)

        e = discord.Embed(colour=colour, description=message)
        if author.avatar_url:
            e.set_author(name=description, icon_url=author.avatar_url)
        else:
            e.set_author(name=description)
        e.set_footer(text=footer)

        try:
            await self.bot.send_message(owner, embed=e)
        except discord.InvalidArgument:
            await self.bot.say("I cannot send your message, I'm unable to find"
                               " my owner... *sigh*")
        except discord.HTTPException:
            await self.bot.say("Your message is too long.")
        except:
            await self.bot.say("I'm unable to deliver your message. Sorry.")
        else:
            await self.bot.say("Your message has been sent.")

    @commands.command()
    async def about(self):
        """grand kiwi bot의 정보를 알려줍니다!"""
        author_repo = "https://github.com/Twentysix26"
        red_repo = author_repo + "/Red-DiscordBot"
        server_url = "https://discord.gg/red"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        since = datetime.datetime(2016, 1, 2, 0, 0)
        days_since = (datetime.datetime.utcnow() - since).days
        dpy_version = "[{}]({})".format(discord.__version__, dpy_repo)
        py_version = "[{}.{}.{}]({})".format(*os.sys.version_info[:3],
                                             python_url)

        owner_set = self.bot.settings.owner is not None
        owner = self.bot.settings.owner if owner_set else None
        if owner:
            owner = discord.utils.get(self.bot.get_all_members(), id=owner)
            if not owner:
                try:
                    owner = await self.bot.get_user_info(self.bot.settings.owner)
                except:
                    owner = None
        if not owner:
            owner = "Unknown"

        about = (
            "grand kiwi bot은 레드봇이라는 오픈 소스의 봇을 사용 하였고"
            "[다운로드는 여기서 가능합니다!]({})"
            "이 봇을 만든 분은 [Twentysix]({}) 이라는 분이시며 꽤 레드봇이 유명합니다.\n\n"
            "혹여나 레드봇에 관심을 가지시거나 "
            "궁금한점은 [레드봇 공식 디스코드]({}) 에 들어 가셔서"
            "질문이나 그외 도움을 받으세요! Good Luck! ㅁㄴㅇㄹ\n\n"
            "".format(red_repo, author_repo, server_url))

        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name="봇 소유자", value=str(owner))
        embed.add_field(name="파이썬 버젼", value=py_version)
        embed.add_field(name="discord.py 버젼", value=dpy_version)
        embed.add_field(name="grand kiwi bot 소스에 대해서", value=about, inline=False)
        embed.set_footer(text="레드봇은 2016년 1월 2일에 태어났습니다! ("
                         "{} 일전!)".format(days_since))

        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command()
    async def uptime(self):
        """Shows Red's uptime"""
        since = self.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        passed = self.get_bot_uptime()
        await self.bot.say("업타임 시간: **{}** (since {} UTC)"
                           "".format(passed, since))

    @commands.command()
    async def version(self):
        """Shows Red's current version"""
        response = self.bot.loop.run_in_executor(None, self._get_version)
        result = await asyncio.wait_for(response, timeout=60)
        try:
            await self.bot.say(embed=result)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def traceback(self, ctx, public: bool=False):
        """Sends to the owner the last command exception that has occurred

        If public (yes is specified), it will be sent to the chat instead"""
        if not public:
            destination = ctx.message.author
        else:
            destination = ctx.message.channel

        if self.bot._last_exception:
            for page in pagify(self.bot._last_exception):
                await self.bot.send_message(destination, box(page, lang="py"))
        else:
            await self.bot.say("No exception has occurred yet.")

    def _populate_list(self, _list):
        """Used for both whitelist / blacklist

        Returns a paginated list"""
        users = []
        total = len(_list)

        for user_id in _list:
            user = discord.utils.get(self.bot.get_all_members(), id=user_id)
            if user:
                users.append("{} ({})".format(user, user.id))

        if users:
            not_found = total - len(users)
            users = ", ".join(users)
            if not_found:
                users += "\n\n ... and {} users I could not find".format(not_found)
            return list(pagify(users, delims=[" ", "\n"]))

        return []

    def _load_cog(self, cogname):
        if not self._does_cogfile_exist(cogname):
            raise CogNotFoundError(cogname)
        try:
            mod_obj = importlib.import_module(cogname)
            importlib.reload(mod_obj)
            self.bot.load_extension(mod_obj.__name__)
        except SyntaxError as e:
            raise CogLoadError(*e.args)
        except:
            raise

    def _unload_cog(self, cogname, reloading=False):
        if not reloading and cogname == "cogs.owner":
            raise OwnerUnloadWithoutReloadError(
                "Can't unload the owner plugin :P")
        try:
            self.bot.unload_extension(cogname)
        except:
            raise CogUnloadError

    def _list_cogs(self):
        cogs = [os.path.basename(f) for f in glob.glob("cogs/*.py")]
        return ["cogs." + os.path.splitext(f)[0] for f in cogs]

    def _does_cogfile_exist(self, module):
        if "cogs." not in module:
            module = "cogs." + module
        if module not in self._list_cogs():
            return False
        return True

    def _wait_for_answer(self, author):
        print(author.name + " requested to be set as owner. If this is you, "
              "type 'yes'. Otherwise press enter.")
        print()
        print("*DO NOT* set anyone else as owner. This has security "
              "repercussions.")

        choice = "None"
        while choice.lower() != "yes" and choice == "None":
            choice = input("> ")

        if choice == "yes":
            self.bot.settings.owner = author.id
            self.bot.settings.save_settings()
            print(author.name + " has been set as owner.")
            self.setowner_lock = False
            self.owner.hidden = True
        else:
            print("The set owner request has been ignored.")
            self.setowner_lock = False

    def _get_version(self):
        if not os.path.isdir(".git"):
            msg = "This instance of Red hasn't been installed with git."
            e = discord.Embed(title=msg,
                              colour=discord.Colour.red())
            return e

        commands = " && ".join((
            r'git config --get remote.origin.url',         # Remote URL
            r'git rev-list --count HEAD',                  # Number of commits
            r'git rev-parse --abbrev-ref HEAD',            # Branch name
            r'git show -s -n 3 HEAD --format="%cr|%s|%H"'  # Last 3 commits
        ))
        result = os.popen(commands).read()
        url, ncommits, branch, commits = result.split("\n", 3)
        if url.endswith(".git"):
            url = url[:-4]
        if url.startswith("git@"):
            domain, _, resource = url[4:].partition(':')
            url = 'https://{}/{}'.format(domain, resource)
        repo_name = url.split("/")[-1]

        embed = discord.Embed(title="Updates of " + repo_name,
                              description="Last three updates",
                              colour=discord.Colour.red(),
                              url="{}/tree/{}".format(url, branch))

        for line in commits.split('\n'):
            if not line:
                continue
            when, commit, chash = line.split("|")
            commit_url = url + "/commit/" + chash
            content = "[{}]({}) - {} ".format(chash[:6], commit_url, commit)
            embed.add_field(name=when, value=content, inline=False)

        embed.set_footer(text="Total commits: " + ncommits)

        return embed

    def get_bot_uptime(self, *, brief=False):
        # Courtesy of Danny
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    def save_global_ignores(self):
        dataIO.save_json("data/red/global_ignores.json", self.global_ignores)

    def save_disabled_commands(self):
        dataIO.save_json("data/red/disabled_commands.json", self.disabled_commands)


def _import_old_data(data):
    """Migration from mod.py"""
    try:
        data["blacklist"] = dataIO.load_json("data/mod/blacklist.json")
    except FileNotFoundError:
        pass

    try:
        data["whitelist"] = dataIO.load_json("data/mod/whitelist.json")
    except FileNotFoundError:
        pass

    return data


def check_files():
    if not os.path.isfile("data/red/disabled_commands.json"):
        print("Creating empty disabled_commands.json...")
        dataIO.save_json("data/red/disabled_commands.json", [])

    if not os.path.isfile("data/red/global_ignores.json"):
        print("Creating empty global_ignores.json...")
        data = {"blacklist": [], "whitelist": []}
        try:
            data = _import_old_data(data)
        except Exception as e:
            log.error("Failed to migrate blacklist / whitelist data from "
                      "mod.py: {}".format(e))

        dataIO.save_json("data/red/global_ignores.json", data)


def setup(bot):
    check_files()
    n = Owner(bot)
    bot.add_cog(n)
