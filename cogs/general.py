import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions, italics, pagify
from random import randint
from random import choice
from enum import Enum
from urllib.parse import quote_plus
from datetime import timezone
from pytz import timezone
import datetime
import time
import aiohttp
import asyncio

settings = {"POLL_DURATION" : 60}


class RPS(Enum):
    rock     = "\N{MOYAI}"
    paper    = "\N{PAGE FACING UP}"
    scissors = "\N{BLACK SCISSORS}"


class RPSParser:
    def __init__(self, argument):
        argument = argument.lower()
        if argument == "주먹":
            self.choice = RPS.rock
        elif argument == "보":
            self.choice = RPS.paper
        elif argument == "가위":
            self.choice = RPS.scissors
        else:
            raise


class General:
    """General commands."""

    def __init__(self, bot):
        self.bot = bot
        self.stopwatches = {}
        self.poll_sessions = []
        self.data = dataIO.load_json('data/server.region/region.json')

    @commands.command()
    async def choose(self, *choices):
        """Chooses between multiple choices.

        To denote multiple choices, you should use double quotes.
        """
        choices = [escape_mass_mentions(c) for c in choices]
        if len(choices) < 2:
            await self.bot.say('Not enough choices to pick from.')
        else:
            await self.bot.say(choice(choices))

    @commands.command(pass_context=True)
    async def roll(self, ctx, number : int = 100):
        """Rolls random number (between 1 and user choice)

        Defaults to 100.
        """
        author = ctx.message.author
        if number > 1:
            n = randint(1, number)
            await self.bot.say("{} :game_die: {} :game_die:".format(author.mention, n))
        else:
            await self.bot.say("{} Maybe higher than 1? ;P".format(author.mention))

    @commands.command(pass_context=True)
    async def 가위바위보(self, ctx, your_choice : RPSParser):
        """봇 vs 당신"""
        author = ctx.message.author
        player_choice = your_choice.choice
        red_choice = choice((RPS.rock, RPS.paper, RPS.scissors))
        cond = {
                (RPS.rock,     RPS.paper)    : False,
                (RPS.rock,     RPS.scissors) : True,
                (RPS.paper,    RPS.rock)     : True,
                (RPS.paper,    RPS.scissors) : False,
                (RPS.scissors, RPS.rock)     : False,
                (RPS.scissors, RPS.paper)    : True
               }

        if red_choice == player_choice:
            outcome = None # Tie
        else:
            outcome = cond[(player_choice, red_choice)]

        if outcome is True:
            await self.bot.say("{}님! 당신이 이겼어요! ~~재수없어~~ \n 봇 : {}"
                               "".format(author.mention, red_choice.value))
        elif outcome is False:
            await self.bot.say("{}님! 당신이 졌어요!  \n 봇 : {} \n ~~깝치기는~~"
                               "".format(author.mention, red_choice.value))
        else:
            await self.bot.say("{}님! 비겼어요! \n 봇 : {}"
                               "".format(author.mention, red_choice.value))

    @commands.command(aliases=["sw"], pass_context=True)
    async def stopwatch(self, ctx):
        """Starts/stops stopwatch"""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await self.bot.say(author.mention + " Stopwatch started!")
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(datetime.timedelta(seconds=tmp))
            await self.bot.say(author.mention + " Stopwatch stopped! Time: **" + tmp + "**")
            self.stopwatches.pop(author.id, None)

    @commands.command()
    async def lmgtfy(self, *, search_terms : str):
        """Creates a lmgtfy link"""
        search_terms = escape_mass_mentions(search_terms.replace("+","%2B").replace(" ", "+"))
        await self.bot.say("https://lmgtfy.com/?q={}".format(search_terms))

    @commands.command(no_pm=True, hidden=True)
    async def hug(self, user : discord.Member, intensity : int=1):
        """Because everyone likes hugs

        Up to 10 intensity levels."""
        name = italics(user.display_name)
        if intensity <= 0:
            msg = "(っ˘̩╭╮˘̩)っ" + name
        elif intensity <= 3:
            msg = "(っ´▽｀)っ" + name
        elif intensity <= 6:
            msg = "╰(*´︶`*)╯" + name
        elif intensity <= 9:
            msg = "(つ≧▽≦)つ" + name
        elif intensity >= 10:
            msg = "(づ￣ ³￣)づ{} ⊂(´・ω・｀⊂)".format(name)
        await self.bot.say(msg)
    
    @commands.command(pass_context=True, no_pm=True)
    async def userinfo(self, ctx, *, user: discord.Member=None):
        """유저의 정보를 보여줍니다"""
        author = ctx.message.author
        server = ctx.message.server

        if not user:
            user = author

        roles = [x.name for x in user.roles if x.name != "@everyone"]

        joined_at = self.fetch_joined_at(user, server)
        since_created = (ctx.message.timestamp - user.created_at).days
        since_joined = (ctx.message.timestamp - joined_at).days
        user_joined = joined_at.strftime("%Y-%m-%d %H:%M")
        user_created = user.created_at.strftime("%Y-%m-%d %H:%M")
        member_number = sorted(server.members,
                               key=lambda m: m.joined_at).index(user) + 1

        created_on = "{}\n({} 일전)".format(user_created, since_created)
        joined_on = "{}\n({} 일전)".format(user_joined, since_joined)

        game = "{}".format(user.status)

        if game is 'online':
            game = '온라인'
        else:
            pass

        if game is 'idle':
            game = '자리 비움'
        else:
            pass

        if game is 'offline':
            game = '오프라인'
        else:
            pass

        if game is 'dnd':
            game = '바쁨'
        else:
            pass
        
        if game is 'Spotify':
            game = 'Spotify 에서 노래 듣는중'
        else:
            pass

        if user.game is None:
            pass
        elif user.game.url is None:
            game = "{}를 플레이중".format(user.game)
        elif user.game is "Spotify":
            game = 'Spotify 에서 노래 듣는중'
        else:
            game = "[{}]에서 ({})를 하는중".format(user.game, user.game.url)

        if roles:
            roles = sorted(roles, key=[x.name for x in server.role_hierarchy
                                       if x.name != "@everyone"].index)
            roles = ", ".join(roles)
        else:
            roles = "없음"

        data = discord.Embed(description=game, colour=user.colour)
        data.add_field(name="디스코드 가입한 날짜", value=created_on)
        data.add_field(name="서버 접속 날짜", value=joined_on)
        data.add_field(name="역할", value=roles, inline=False)
        data.set_footer(text="#{}번째 유저 | ID:{}"
                             "".format(member_number, user.id))

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar_url:
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        else:
            data.set_author(name=name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True, no_pm=True)
    async def serverinfo(self, ctx):
        """서버의 정보를 보여줍니다!"""
        server = ctx.message.server
        online = len([m.status for m in server.members
                      if m.status != discord.Status.offline])
        region = server.region
        total_users = len(server.members)
        text_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.text])
        voice_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.voice])
        passed = (ctx.message.timestamp - server.created_at).days
        created_at = ("서버 개설일: {} ({}일 전)"
                      "".format(server.created_at.strftime("%Y-%m-%d %H:%M"),
                                passed))

        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        yee = self.data[region]

        game = "{}".format(server.verification_level)

        if region is 'japan':
            region = ':flag_jp: 일본'
        elif region is 'brazil':
            region = ':flag_br: 브라질'
        elif region is 'eu-central':
            region = ':flag_eu: 유럽 중앙부'
        elif region is 'hongkong':
            region = ':flag_hk: 홍콩'
        elif region is 'india':
            region = ':flag_in: 인도'
        elif region is 'eu-west':
            region = ':flag_eu: 유럽 동부'
        elif region is 'us-west':
            region = ':flag_us: 미국 동부'
        elif region is 'us-south':
            region = ':flag_us: 미국 남부'
        elif region is 'us-east':
            region = ':flag_us: 미국 서부'
        elif region is 'us-central':
            region = ':flag_us: 미국 중앙부'
        elif region is 'russia':
            region = ':flag_ru: 러시아'
        elif region is 'singapore':
            region = ':flag_sg: 싱가포르'
        elif region is 'sydney':
            region = ':flag_au: 시드니'
        elif region is 'southafrica':
            region = ':flag_ss: 남 아프리카'
        else:
            pass

        if game is 'none':
            game = '없음\n**(아무 제한도 없어요!)**'
        elif game is 'low':
            game = '낮음\n**(자신의 디스코드 계정이 이메일 인증을 받은적이 있어야 해요!)**'
        elif game is 'medium':
            game = '중간\n**(자신의 디스코드 계정이 이메일 인증을 받은적이 있어야 하고 가입한지 5분이 지나야 합니다!)**'
        elif game is 'high':
            game = '높음\n**(자신의 디스코드 계정이 이메일 인증을 받은적이 있어야 하고 가입한지 5분이 지나야 하고 멤버가 된지 10분이 되어야 합니다!)**'
        elif game is '4':
            game = '**매우 높음\n(전화 인증이 완료된 디스코드 계정 이여야 합니다!)**'
        else:
            pass

        data = discord.Embed(
            description=created_at,
            colour=discord.Colour(value=colour))
        data.add_field(name="서버 위치", value=server.region)
        data.add_field(name="유저 수", value="{}명".format(len(server.members)))
        data.add_field(name="채팅 채널 수", value=text_channels)
        data.add_field(name="음성 채널 수", value=voice_channels)
        data.add_field(name="역할", value=len(server.roles))
        data.add_field(name='보안 단계', value=game)
        data.add_field(name="주인", value=str(server.owner))
        data.set_footer(text="서버 ID: " + server.id)

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("`Embed links`권한이 있어야 서버 정보를"
                               "보낼 수 있어요")

    @commands.command(pass_context=True, no_pm=True)
    async def channelinfo(self, ctx, channel: discord.Channel=None):
        """채팅방 정보를 불러오는 명령어입니다!"""
        user = ctx.message.author
        if not channel:
            channel = ctx.message.channel
        else:
            pass
        channeltype = channel.type
        channeltopic = channel.topic
        passed = (ctx.message.timestamp - channel.created_at).days
        created_at = ("채널 개설일: {} ({}일 전)"
                      "".format(channel.created_at.strftime("%Y-%m-%d %H:%M"),
                                passed))
        if channeltype is 'text':
            channeltype = '글 채널'
        else:
            channeltype = '음성 채널'
        em = discord.Embed(title='Channelinfo',colour=user.colour)
        em.add_field(name='채널 멘션', value=channel.mention)
        em.add_field(name='채널 ID', value=channel.id)
        em.add_field(name='채널 주제', value=channeltopic)
        em.add_field(name='채널 종류', value=channeltype)
        em.add_field(name='채널 생성 날짜', value=created_at)
        await self.bot.say(embed=em)
            

    @commands.command()
    async def urban(self, *, search_terms : str, definition_number : int=1):
        """Urban Dictionary search

        Definition number must be between 1 and 10"""
        def encode(s):
            return quote_plus(s, encoding='utf-8', errors='replace')

        # definition_number is just there to show up in the help
        # all this mess is to avoid forcing double quotes on the user

        search_terms = search_terms.split(" ")
        try:
            if len(search_terms) > 1:
                pos = int(search_terms[-1]) - 1
                search_terms = search_terms[:-1]
            else:
                pos = 0
            if pos not in range(0, 11): # API only provides the
                pos = 0                 # top 10 definitions
        except ValueError:
            pos = 0

        search_terms = "+".join([encode(s) for s in search_terms])
        url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
        try:
            async with aiohttp.get(url) as r:
                result = await r.json()
            if result["list"]:
                definition = result['list'][pos]['definition']
                example = result['list'][pos]['example']
                defs = len(result['list'])
                msg = ("**Definition #{} out of {}:\n**{}\n\n"
                       "**Example:\n**{}".format(pos+1, defs, definition,
                                                 example))
                msg = pagify(msg, ["\n"])
                for page in msg:
                    await self.bot.say(page)
            else:
                await self.bot.say("Your search terms gave no results.")
        except IndexError:
            await self.bot.say("There is no definition #{}".format(pos+1))
        except:
            await self.bot.say("Error.")

    @commands.command(pass_context=True, no_pm=True)
    async def poll(self, ctx, *text):
        """Starts/stops a poll

        Usage example:
        poll Is this a poll?;Yes;No;Maybe
        poll stop"""
        message = ctx.message
        if len(text) == 1:
            if text[0].lower() == "stop":
                await self.endpoll(message)
                return
        if not self.getPollByChannel(message):
            check = " ".join(text).lower()
            if "@everyone" in check or "@here" in check:
                await self.bot.say("Nice try.")
                return
            p = NewPoll(message, " ".join(text), self)
            if p.valid:
                self.poll_sessions.append(p)
                await p.start()
            else:
                await self.bot.say("poll question;option1;option2 (...)")
        else:
            await self.bot.say("A poll is already ongoing in this channel.")

    async def endpoll(self, message):
        if self.getPollByChannel(message):
            p = self.getPollByChannel(message)
            if p.author == message.author.id: # or isMemberAdmin(message)
                await self.getPollByChannel(message).endPoll()
            else:
                await self.bot.say("Only admins and the author can stop the poll.")
        else:
            await self.bot.say("There's no poll ongoing in this channel.")

    def getPollByChannel(self, message):
        for poll in self.poll_sessions:
            if poll.channel == message.channel:
                return poll
        return False

    async def check_poll_votes(self, message):
        if message.author.id != self.bot.user.id:
            if self.getPollByChannel(message):
                    self.getPollByChannel(message).checkAnswer(message)

    def fetch_joined_at(self, user, server):
        """Just a special case for someone special :^)"""
        if user.id == "96130341705637888" and server.id == "133049272517001216":
            return datetime.datetime(2016, 1, 10, 6, 8, 4, 443000)
        else:
            return user.joined_at

class NewPoll():
    def __init__(self, message, text, main):
        self.channel = message.channel
        self.author = message.author.id
        self.client = main.bot
        self.poll_sessions = main.poll_sessions
        msg = [ans.strip() for ans in text.split(";")]
        if len(msg) < 2: # Needs at least one question and 2 choices
            self.valid = False
            return None
        else:
            self.valid = True
        self.already_voted = []
        self.question = msg[0]
        msg.remove(self.question)
        self.answers = {}
        i = 1
        for answer in msg: # {id : {answer, votes}}
            self.answers[i] = {"ANSWER" : answer, "VOTES" : 0}
            i += 1

    async def start(self):
        msg = "**POLL STARTED!**\n\n{}\n\n".format(self.question)
        for id, data in self.answers.items():
            msg += "{}. *{}*\n".format(id, data["ANSWER"])
        msg += "\nType the number to vote!"
        await self.client.send_message(self.channel, msg)
        await asyncio.sleep(settings["POLL_DURATION"])
        if self.valid:
            await self.endPoll()

    async def endPoll(self):
        self.valid = False
        msg = "**POLL ENDED!**\n\n{}\n\n".format(self.question)
        for data in self.answers.values():
            msg += "*{}* - {} votes\n".format(data["ANSWER"], str(data["VOTES"]))
        await self.client.send_message(self.channel, msg)
        self.poll_sessions.remove(self)

    def checkAnswer(self, message):
        try:
            i = int(message.content)
            if i in self.answers.keys():
                if message.author.id not in self.already_voted:
                    data = self.answers[i]
                    data["VOTES"] += 1
                    self.answers[i] = data
                    self.already_voted.append(message.author.id)
        except ValueError:
            pass

def setup(bot):
    n = General(bot)
    bot.add_listener(n.check_poll_votes, "on_message")
    bot.add_cog(n)
