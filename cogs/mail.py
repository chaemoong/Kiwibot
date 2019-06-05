import discord, datetime, os, time
from discord.ext import commands

class mail:
    """asdf!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def mail(self, ctx, 유저:discord.Member, title, *, text=None):
        """메일을 전송합니다!"""
        server = ctx.message.server
        user = ctx.message.author
        if 유저:
            if title:
                if text:
                    e=discord.Embed(colour=discord.Colour.green(), Title='메일이 도착했습니다!')
                    if 유저.avatar_url:
                        e.set_thumbnail(url=유저.avatar_url)
                    e.add_field(name='제목', value=title, inline=False)
                    e.add_field(name='보낸 사람', value=user, inline=False)
                    e.add_field(name='내용', value=text, inline=False)
                    await self.bot.send_message(유저, embed=e)
                    await self.bot.say('메일이 전송되었습니다!')
                else:
                    await self.bot.say('보낼 메시지를 작성하세요!')
            else:
                await self.bot.say('제목을 작성하셔야 합니다!')
        else:
            await self.bot.say('유저를 멘션 하셔야 합니다!')



def setup(bot):
    n = mail(bot)
    bot.add_cog(n)
