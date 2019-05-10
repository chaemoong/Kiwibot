import discord
from discord.ext import commands
import time


class Ping:
    """a semi-actual ping"""

    def __init__(self,bot):
        self.bot = bot


    @commands.command(aliases=["핑", "vld", "ㅔㅑㅜㅎ"], pass_context=True)
    async def ping(self,ctx):
        """봇의 핑을 확인합니다!"""
        channel = ctx.message.channel
        t1 = time.perf_counter()
        await self.bot.send_typing(channel)
        t2 = time.perf_counter()
        em = discord.Embed(colour=discord.Colour.purple())
        em.add_field(name='핑', value='퐁! :ping_pong: 봇의 핑 : {}ms'.format(round((t2-t1)*1000)))
        await self.bot.say(embed=em)
        
def setup(bot):
    bot.add_cog(Ping(bot))
