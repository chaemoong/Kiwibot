import discord, datetime, os, time
from discord.ext import commands
from cogs.utils.dataIO import dataIO


class Afk:
    """asdf!"""

    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.profile = "data/afk/afk.json"
        self.riceCog = dataIO.load_json(self.profile)
        self.ko = "data/language/ko_kr.json"
        self.ko_kr = dataIO.load_json(self.ko)
        self.en = "data/language/en_us.json"
        self.en_us = dataIO.load_json(self.en)
        
    @commands.command(no_pm=True, pass_context=True)
    async def afk(self, ctx, *, reason=None):
        """잠수 명령어 입니다! \n 많이 부족하지만... 많이 사용해주세요!"""
        timedata = datetime
        dt = datetime.datetime.now()
        author = ctx.message.author
        server = ctx.message.server
        user = author
        mod = self.bot.get_cog('Mod')
        try:
            language = mod.settings[server.id]['languages']
        except KeyError:
            language = 'en'
        if language is 'ko':
            yee = self.ko_kr['afk']
        elif language is 'en':
            yee = self.en_us['afk']
        else:
            yee = self.en_us['afk']
        self.data[author.id] = int(time.perf_counter())
        afkstart = discord.Embed(colour=user.colour)
        afkstart.add_field(name=yee['field'], value=yee['value'].format(author.name))
        afkstart.set_footer(text=yee['footer'].format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        if not reason:
            self.riceCog[user.id] = {}
            self.riceCog[user.id].update({"reason": None})
            dataIO.save_json(self.profile,
                         self.riceCog)
            await self.bot.say(embed=afkstart)
        elif '```\n' in reason or '```' in reason:
            await self.bot.say("당신은 키위봇 afk 명렁어 사용법 위반으로 블랙리스트에 추가되었습니다!\n이것에 관하여 문의가 있으면 chaemoong#8612으로 문의 해주시기 바랍니다")
            try:
                cog = self.bot.get_cog('Owner')
                cog.global_ignores["blacklist"].append(author.id)
                cog.save_global_ignores()
                mod = self.bot.get_cog('Mod')
                mod_channel = server.get_channel(mod.settings[server.id]["mod-log"])
                await self.bot.send_message(mod_channel, '**처리번호 #**:thinking: | 블랙리스트\n**유저:** {} ({})\n**관리자:** {} ({})\n**사유:** 키위봇 afk 기능 사용법 위반'.format(author, author.id, self.bot.user, self.bot.user.id))
            except:
                pass
        else:
            try:
                afkstart.add_field(name=yee['reason'], value='```\n{}\n```'.format(reason), inline=False)
                self.riceCog[user.id] = {}
                self.riceCog[user.id].update({"reason": reason})
                dataIO.save_json(self.profile,
                             self.riceCog)
                await self.bot.say(embed=afkstart)
            except:
                pass

    async def on_message(self, message):
        author = message.author
        dt = datetime.datetime.now()
        user = author
        tmp = {}
        mod = self.bot.get_cog('Mod')
        try:
            language = mod.settings[user.server.id]['languages']
        except:
            language = 'en'
        if language is 'ko':
            yee = self.ko_kr['afk_end']
            asdf = self.ko_kr['afk_ing']
        elif language is 'en':
            yee = self.en_us['afk_end']
            asdf = self.en_us['afk_ing']
        else:
            yee = self.en_us['afk_end']
            asdf = self.en_us['afk_ing']
        for mention in message.mentions:
            tmp[mention] = True
        if message.author.id != self.bot.user.id:
            for author in tmp:
                if author.id in self.riceCog:
                    try:
                        avatar = author.avatar_url if author.avatar else author.default_avatar_url
                        if self.riceCog[author.id]['reason']:
                            em = discord.Embed(color=author.colour)
                            em.add_field(name=asdf['reason'], value=self.riceCog[author.id]['reason'])
                            em.set_author(name=asdf['author'].format(author.display_name), icon_url=avatar)
                        else:
                            em = discord.Embed(color=author.colour)
                            em.add_field(name=asdf['reason'], value=asdf['reason_None'])
                            em.set_author(name=asdf['author'].format(author.display_name), icon_url=avatar)
                        await self.bot.send_message(message.channel, embed=em)
                    except:
                        await self.bot.send_message(message.channel, '봇 권한 중에서 `링크 첨부` 권한이 빠져있습니다!\n봇 권한을 추가해주세요!')
        if user.id in self.riceCog:
            try:
                tmp = abs(self.data[author.id] - int(time.perf_counter()))
                tmp1 = str(datetime.timedelta(seconds=tmp))
                reason = self.riceCog[user.id]["reason"]
                if tmp > 0:
                    if reason is None:
                        reason = yee['reason-none']
                    else:
                        if language is 'ko':
                            reason = reason + yee['reason-yes']
                        elif language is 'en':
                            reason = reason
                        else:
                            reason = reason
                    afkend = discord.Embed(
                        colour=user.colour
                    )                
                    afkend.add_field(name=yee['field'].format(author.name), value=yee['value'].format(author.name, tmp1, reason), inline=False)
                    afkend.add_field(name=yee['footer'], value='{}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second), inline=False)
                    await self.bot.send_message(message.channel, embed=afkend)
                    self.data.pop(author.id)
                    del self.riceCog[user.id]
                    dataIO.save_json(self.profile,
                                 self.riceCog)   
            except:
                pass
        else:
            pass
                
def check_folder():
    if not os.path.exists('data/afk'):
        print('data/afk 풀더생성을 완료하였습니다!')
        os.makedirs('data/afk')

def check_file():
    data = {}
    f = "data/afk/afk.json"
    if not dataIO.is_valid_json(f):
        print("afk.json 파일생성을 완료하였습니다!")
        dataIO.save_json(f,
                         data)


def setup(bot):
    check_folder()
    check_file()
    n = Afk(bot)
    bot.add_cog(n)
