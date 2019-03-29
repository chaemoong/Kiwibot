import requests, discord, os
from bs4 import BeautifulSoup
from discord.ext import commands
from cogs.utils.dataIO import dataIO

class melon:
    """asdf"""

    def __init__(self, bot):
        self.bot = bot
        self.profile = 'data/melon/melon.json'
        self.riceCog = dataIO.load_json(self.profile)

    @commands.command(pass_context=True)
    async def melon(self, ctx):
        """asdf"""
        RANK = 10

    
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        req = requests.get('https://www.melon.com/chart/index.htm', headers = header)
        html = req.text
        parse = BeautifulSoup(html, 'html.parser')
        
        titles = parse.find_all("div", {"class": "ellipsis rank01"})
        songs = parse.find_all("div", {"class": "ellipsis rank02"})
        
        title = []
        song = []
    
        for t in titles:
            title.append(t.find('a').text)
    
        for s in songs:
            song.append(s.find('span', {"class": "checkEllipsis"}).text)
        
        for i in range(RANK):
            self.riceCog = {}
            self.riceCog.update({"info": '%s - %s'%(i+1, title[i], song[i])})
            dataIO.save_json(self.profile,
                        self.riceCog)
            meloninfo = self.riceCog["info"]
            em = discord.Embed(colour=0x80ff80)
            em.add_field(name='%3d위'%(i+1), value=meloninfo)
            await self.bot.say(embed=em)

def check_folder():
    if not os.path.exists('data/melon'):
        print('data/melon 풀더생성을 완료하였습니다!')
        os.makedirs('data/melon')

def check_file():
    data = {}
    f = "data/melon/melon.json"
    if not dataIO.is_valid_json(f):
        print("melon.json 파일생성을 완료하였습니다!")
        dataIO.save_json(f,
                         data)


def setup(bot):
    check_folder()
    check_file()
    n = melon(bot)
    bot.add_cog(n)  