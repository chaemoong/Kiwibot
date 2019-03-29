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
        
    @commands.command(pass_context=True)
    async def afk(self, ctx, *, reason=None):
        """잠수 명령어 입니다! \n 많이 부족하지만... 많이 사용해주세요!"""
        timedata = datetime
        dt = datetime.datetime.now()
        author = ctx.message.author
        server = ctx.message.server
        user = author
        self.data[author.id] = int(time.perf_counter())
        afkstart = discord.Embed(colour=user.colour)
        afkstart.add_field(name='잠수 시작!', value='{} 님의 잠수가 시작되었습니다!\n잠수 상태를 해제 하고 싶을시 아주 메시지나 작성 하시면 됩니다!'.format(author.name))
        afkstart.set_footer(text='잠수 시작 시간 {}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        afkstart_reason = discord.Embed(
            colour=user.colour        
            )
        afkstart_reason.add_field(name='잠수 시작!', value='{} 님의 잠수가 시작되었습니다!\n잠수 상태를 해제 하고 싶을시 아주 메시지나 작성 하시면 됩니다!'.format(author.name))
        afkstart_reason.add_field(name='사유', value='```\n{}\n```'.format(reason))
        afkstart_reason.set_footer(text='잠수 시작 시간 {}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        if not reason:
            self.riceCog[user.id] = {}
            self.riceCog[user.id].update({"reason": None})
            dataIO.save_json(self.profile,
                         self.riceCog)
            await self.bot.say(embed=afkstart)
        else:
            try:
                self.riceCog[user.id] = {}
                self.riceCog[user.id].update({"reason": reason})
                dataIO.save_json(self.profile,
                             self.riceCog)
                await self.bot.say(embed=afkstart_reason)
            except:
                pass

    async def on_message(self, message):
        author = message.author
        dt = datetime.datetime.now()
        user = author
        tmp = {}
        for mention in message.mentions:
            tmp[mention] = True
        if message.author.id != self.bot.user.id:
            for author in tmp:
                if author.id in self.riceCog:
                    try:
                        avatar = author.avatar_url if author.avatar else author.default_avatar_url
                        if self.riceCog[author.id]['reason']:
                            em = discord.Embed(color=author.colour)
                            em.add_field(name='사유', value=self.riceCog[author.id]['reason'])
                            em.set_author(name='{}님은 현재 잠수 상태입니다!'.format(author.display_name), icon_url=avatar)
                        else:
                            em = discord.Embed(color=author.colour)
                            em.add_field(name='사유', value='없음')
                            em.set_author(name='{} 님은 현재 잠수 상태입니다!'.format(author.display_name), icon_url=avatar)
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
                        reason = '없습니다'
                    else:
                        reason = reason + ' 입니다'
                    afkend = discord.Embed(
                        colour=user.colour
                    )                
                    afkend.add_field(name='{}님의 잠수상태가 종료되었습니다!'.format(author.name), value='**{}님의 잠수 기간은 {} 이며, 사유는 {}**'.format(author.name, tmp1, reason))
                    afkend.add_field(name='잠수 종료 시간', value='{}-{}-{} {}:{}:{}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
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