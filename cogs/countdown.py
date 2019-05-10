from discord.ext import commands
import asyncio
import calendar
import time

class countdown:
    """Countdown timer!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True)
    async def timer(self, ctx, seconds, *, title):
        counter = 0
        try:
            secondint = int(seconds)
            finish = getEpoch(secondint)
            if secondint < 0 or secondint == 0:
                await self.bot.say("I dont think im allowed to do negatives \U0001f914")
                raise BaseException

            message = await self.bot.say("```css" + "\n" + "[" + title +"]" + "\n타이머: " + remaining(finish)[0] + "```")
            channelID = ctx.message.channel.id
            msgID = message.id
            while True:
                channel = self.bot.get_channel(channelID)
                message = await self.bot.get_message(channel, msgID)
                timer, done = remaining(finish)
                if done:
                    await self.bot.edit_message(message, new_content=("```끝!```"))
                    break
                await self.bot.edit_message(message, new_content=("```css" + "\n" + "[" + title + "]" + "\n시간: {0}```".format(timer)))
                await asyncio.sleep(1)
            await self.bot.send_message(ctx.message.channel, ctx.message.author.mention +  "[" + title + "]"  + "가 주제인 타이머가 끝났습니다!")
        except ValueError:
            await self.bot.say("타이머를 몇초를 할지 정해야 합니다!!")

def setup(bot):
    n = countdown(bot)
    bot.add_cog(n)

def remaining(epoch):
    remaining = epoch - time.time()
    finish = (remaining < 0)
    m, s = divmod(remaining, 60)
    h, m = divmod(m, 60)
    s = int(s)
    m = int(m)
    h = int(h)
    out = "{:01d}:{:02d}:{:02d}".format(h, m, s)
    return out, finish

def getEpoch(seconds : int):
    epoch = time.time()
    epoch += seconds
    return epoch
