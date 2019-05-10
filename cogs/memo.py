import discord, os
from discord.ext import commands
from cogs.utils.dataIO import dataIO

class memo:
    """asdf"""

    def __init__(self, bot):
        self.bot = bot
        self.profile = "data/memo/memo.json"
        self.riceCog = dataIO.load_json(self.profile)

    @commands.command(no_pm=True, pass_context=True)
    async def memo(self, ctx, *, memo=None):
        """메모를 추가하는 기능입니다!"""
        user = ctx.message.author
        try:
            if memo is None:
                try:
                    memo = self.riceCog[user.id]["memo"]
                    em = discord.Embed(colour=0x2ecc71)
                    em.add_field(name='메모 내용', value='메모: {}'.format(memo))
                    if user.avatar_url:
                        em.set_thumbnail(url=user.avatar_url)
                    else:
                        pass
                except KeyError:
                    em = discord.Embed(colour=0x2ecc71, title='메모가 없습니다!')
                    if user.avatar_url:
                        em.set_thumbnail(url=user.avatar_url)
                    else:
                        pass
                await self.bot.say(embed=em)
            else:
                try:
                    del self.riceCog[user.id]
                    em = discord.Embed(colour=0x2ecc71, title='메모가 업데이트 되었습니다!')
                    em.add_field(name='메모 작성', value='메모: {}'.format(memo))
                    if user.avatar_url:
                        em.set_thumbnail(url=user.avatar_url)
                    else:
                        pass
                    self.riceCog[user.id] = {}
                    self.riceCog[user.id].update({"memo": memo})
                    dataIO.save_json(self.profile,
                                self.riceCog)
                    await self.bot.say(embed=em)
                except KeyError:
                    em = discord.Embed(colour=0x2ecc71, title='메모가 업데이트 되었습니다!')
                    em.add_field(name='메모 작성', value='메모: {}'.format(memo))
                    if user.avatar_url:
                        em.set_thumbnail(url=user.avatar_url)
                    else:
                        pass
                    self.riceCog[user.id] = {}
                    self.riceCog[user.id].update({"memo": memo})
                    dataIO.save_json(self.profile,
                                self.riceCog)
                    await self.bot.say(embed=em)
        except discord.HTTPException:
            await self.bot.say('봇에 권한이 부족합니다!\n봇에게 관리자 권한을 주시기 바랍니다!')

def check_folder():
    if not os.path.exists('data/memo'):
        print('data/memo 풀더생성을 완료하였습니다!')
        os.makedirs('data/memo')

def check_file():
    data = {}
    f = "data/memo/memo.json"
    if not dataIO.is_valid_json(f):
        print("memo.json 파일생성을 완료하였습니다!")
        dataIO.save_json(f,
                         data)


def setup(bot):
    check_folder()
    check_file()
    n = memo(bot)
    bot.add_cog(n)
