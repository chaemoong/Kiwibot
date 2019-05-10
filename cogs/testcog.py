import discord, datetime, os
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from cogs.utils import checks


class Afk:
    """asdf!"""

    def __init__(self, bot):
        self.bot = bot
        self.ricecog = dataIO.load_json('data/afk/afk.json')


        
    @commands.command(pass_context=True)
    @checks.is_owner()
    async def test(self, ctx, *, reason: str = None):
        """test command never don't use to not owner"""
        dt = datetime.datetime.now()
        reason_yes = (("```diff" + "\n+ {} 님의 잠수상태가 시작되었습니다." + "\n+ 잠수 시작시간은 {}-{}-{} {}:{}:{} 이며, 잠수 사유는 {} 입니다.\n- 현재 사유없이 적으면 사유가 공백으로 보이는것은 곧 수정할 예정입니다!" + "```").format(ctx.message.author.name, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, reason))
        reason_no = (("```diff" + "\n+ {} 님의 잠수상태가 시작되었습니다." + "\n+ 잠수 시작시간은 {}-{}-{} {}:{}:{} 이며, 잠수 사유는 없습니다." + "```").format(ctx.message.author.name, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, reason))
        if reason is None:
            await self.bot.say(reason_no)
        else:
            await self.bot.say(reason_yes)

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