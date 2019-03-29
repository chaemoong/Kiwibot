import discord, os
from discord.ext import commands
from cogs.utils.dataIO import dataIO

class memo:
    """asdf"""

    def __init__(self, bot):
        self.bot = bot
        self.profile = "data/memo/memo.json"
        self.riceCog = dataIO.load_json(self.profile)

    @commands.command(pass_context=True)
    async def memo(self, ctx, *message):
        """메모를 추가하는 기능입니다!"""
        user = ctx.message.author
        try:
            if not message:
                memo = self.riceCog[user.id]["memo"]
                await self.bot.say(memo)
            else:
                self.riceCog[user.id] = {}
                self.riceCog[user.id].update({"memo": message})
                dataIO.save_json(self.profile,
                            self.riceCog)
                await self.bot.say('메모가 업데이트 되었습니다!')
        except KeyError:
            await self.bot.say('메모가 저장되어있지 않습니다!')

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