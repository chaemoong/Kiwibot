import os
import sys
import urllib.request
from discord.ext import commands
import discord
from cogs.utils.dataIO import dataIO

class shortenurl:
    """asdf!"""

    def __init__(self, bot):
        self.bot = bot
        self.data = 'data/url/url.json'
        settings = dataIO.load_json(self.data)


    @commands.command(pass_context=True)
    async def shorten(self, url):
        """네이버 API키를 통하여 긴 주소를 짧은 주소로 변형 시켜주는 명령어 입니다!"""
        client_id = "" # 개발자센터에서 발급받은 Client ID 값
        client_secret = "" # 개발자센터에서 발급받은 Client Secret 값
        m = url
        encText = urllib.parse.quote(m)
        data = "url=" + encText
        api = "https://openapi.naver.com/v1/util/shorturl"
        request = urllib.request.Request(api)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            response_body.decode('utf-8').replace(' 'and':'and',', '')
            b=response_body.decode('utf-8').split('"')
            await self.bot.say(b[13])
        else:
            print("Error Code:" + rescode)


def check_folder():
    if not os.path.exists('data/url'):
        print('data/url 풀더생성을 완료하였습니다!')
        os.makedirs('data/url')

def check_file():
    data = {}
    f = "data/url/url.json"
    if not dataIO.is_valid_json(f):
        print("url.json 파일생성을 완료하였습니다!")
        dataIO.save_json(f,
                         data)

def setup(bot):
    check_folder()
    check_file()
    n = shortenurl(bot)
    bot.add_cog(n)
