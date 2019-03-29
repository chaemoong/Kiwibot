from cogs.utils.checks import is_owner_check
from cogs.downloader import CloningError, RequirementFail, WINDOWS_OS, DISCLAIMER
from urllib.parse import quote
import discord
from discord.ext import commands
import aiohttp


numbs = {
    "next": "➡",
    "back": "⬅",
    "install": "✅",
    "exit": "❌"
}


class Redportal:
    """Interact with cogs.red through your bot"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def __unload(self):
        self.session.close()

    @commands.group(pass_context=True, aliases=['redp'])
    async def redportal(self, ctx):
        """Interact with cogs.red through your bot"""

        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    async def _search_redportal(self, ctx, url):
        # future response dict
        data = None

        try:
            async with self.session.get(url) as response:
                data = await response.json()
        except Exception:
            return None

        if data is not None and not data['error'] and len(data['results']['list']) > 0:
            # a list of embeds
            embeds = []

            for cog in data['results']['list']:
                cog_name = cog['name']
                repo_name = cog['repo']['name']
                repo_url = cog['links']['github']['repo']
                tags = cog['tags'] or []
                description = cog['description'] or cog['short']

                if len(description) > 175:
                    description = '{}...'.format(description[:175])

                embed = discord.Embed(title=cog_name, description=description, color=0xfd0000,
                                      url='https://cogs.red{}'.format(cog['links']['self']))
                embed.add_field(name='종류', value=cog['repo']['type'], inline=True)
                embed.add_field(name='개발한 아저씨', value=cog['author']['name'], inline=True)
                embed.add_field(name='이름', value=repo_name, inline=True)
                embed.add_field(name='추가하는법 1', inline=False,
                                value='{}cog repo add {} {}'.format(ctx.prefix, repo_name, repo_url))
                embed.add_field(name='추가하는법 2', inline=False,
                                value='{}cog install {} {}'.format(ctx.prefix, repo_name, cog_name))
                embed.add_field(name='추가하려면 반응중 ✅를 누르시면 됩니다!', value='ㅁㄴㅇㄹ')
                embed.set_footer(text='{} ⭐ - {}'.format(cog['votes'],
                                                         '🔖 {}'.format(', '.join(tags)) if tags else 'No tags set 😢'))
                embeds.append(embed)

            return embeds, data

        else:
            return None

    @redportal.command(pass_context=True)
    async def search(self, ctx, *, term: str):
        """Searches for a cog"""

        try:
            # base url for the cogs.red search API
            base_url = 'https://cogs.red/api/v1/search/cogs'

            # final request url
            url = '{}/{}'.format(base_url, quote(term))

            embeds, data = await self._search_redportal(ctx, url)

            if embeds is not None:
                await self.cogs_menu(ctx, embeds, message=None, page=0, timeout=30, edata=data)
            else:
                await self.bot.say('No cogs were found or there was an error in the process')

        except TypeError:
            await self.bot.say('No cogs were found or there was an error in the process')

    async def cogs_menu(self, ctx, cog_list: list,
                        message: discord.Message=None,
                        page=0, timeout: int=30, edata=None):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        cog = cog_list[page]

        is_owner_or_co = is_owner_check(ctx)
        if is_owner_or_co:
            expected = ["➡", "✅", "⬅", "❌"]
        else:
            expected = ["➡", "⬅", "❌"]

        if not message:
            message =\
                await self.bot.send_message(ctx.message.channel, embed=cog)
            await self.bot.add_reaction(message, "⬅")
            await self.bot.add_reaction(message, "❌")

            if is_owner_or_co:
                await self.bot.add_reaction(message, "✅")

            await self.bot.add_reaction(message, "➡")
        else:
            message = await self.bot.edit_message(message, embed=cog)
        react = await self.bot.wait_for_reaction(
            message=message, user=ctx.message.author, timeout=timeout,
            emoji=expected
        )
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except Exception:
                    await self.bot.remove_reaction(message, "⬅", self.bot.user)
                    await self.bot.remove_reaction(message, "❌", self.bot.user)
                    if is_owner_or_co:
                        await self.bot.remove_reaction(message, "✅", self.bot.user)
                    await self.bot.remove_reaction(message, "➡", self.bot.user)
            except Exception:
                pass
            return None
        reacts = {v: k for k, v in numbs.items()}
        react = reacts[react.reaction.emoji]
        if react == "next":
            page += 1
            next_page = page % len(cog_list)
            try:
                await self.bot.remove_reaction(message, "➡", ctx.message.author)
            except Exception:
                pass
            return await self.cogs_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout, edata=edata)
        elif react == "back":
            page -= 1
            next_page = page % len(cog_list)
            try:
                await self.bot.remove_reaction(message, "⬅", ctx.message.author)
            except Exception:
                pass
            return await self.cogs_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout, edata=edata)
        elif react == "install":
            if not is_owner_or_co:
                await self.bot.say("This function is only available to the bot owner.")
                return await self.cogs_menu(ctx, cog_list, message=message,
                                            page=page, timeout=timeout, edata=edata)
            else:
                downloader = self.bot.get_cog('Downloader')
                if not downloader:
                    await self.bot.say("The downloader cog must be loaded to use this feature.")
                    return await self.cogs_menu(ctx, cog_list, message=message,
                                                page=page, timeout=timeout, edata=edata)

                repo_name = edata['results']['list'][page]['repo']['name']
                repo_url = edata['results']['list'][page]['links']['github']['repo']
                cog_name = edata['results']['list'][page]['name']

                await self.attempt_install(ctx, downloader, repo_name, repo_url, cog_name)
                return await self.bot.delete_message(message)
        else:
            try:
                return await self.bot.delete_message(message)
            except Exception:
                pass

    async def attempt_install(self, ctx, downloader, repo_name, repo_url, cog_name):
        existing_repo = None
        existing_data = {}
        lower_url = repo_url.lower()
        lower_name = repo_name.lower()

        for r_name, r_data in downloader.repos.items():
            if r_data.get('url', '').lower() == lower_url or r_name.lower() == lower_name:
                repo_name = existing_repo = r_name
                existing_data = r_data
                break

        if not existing_repo:
            await self.bot.say("Repo not added yet, doing so now...")

            if not downloader.disclaimer_accepted:
                await self.bot.say(DISCLAIMER)
                answer = await self.bot.wait_for_message(timeout=30, author=ctx.message.author)

                if answer and "i agree" in answer.content.lower():
                    downloader.disclaimer_accepted = True
                else:
                    await self.bot.say('Not adding repo.')
                    return False

            downloader.repos[repo_name] = {'url': repo_url}
            retval = await self.do_repo_update(downloader, repo_name, just_added=True)

            if not retval:
                return retval

            data = downloader.get_info_data(repo_name)

            if data:
                msg = data.get("INSTALL_MSG")
                if msg:
                    await self.bot.say(msg[:2000])

            await self.bot.say("Repo '{}' added.".format(repo_name))
        elif cog_name not in existing_data:
            retval = await self.do_repo_update(downloader, repo_name)

            if not retval:
                return retval
            elif cog_name not in existing_data:  # repo dict is updated in-place
                await self.bot.say("The cog was not found in the repo data, "
                                   "even after an update. Check your branch.")
                return False
        elif existing_data[cog_name].get("INSTALLED"):
            await self.bot.say("%s is already installed." % cog_name)
            return True

        return await self.do_cog_install(ctx, downloader, repo_name, cog_name)

    async def do_repo_update(self, downloader, repo_name, just_added=False):
        try:
            downloader.update_repo(repo_name)
        except CloningError:
            await self.bot.say("Repository link doesn't seem to be valid.")

            if just_added:
                del downloader.repos[repo_name]

            return False
        except FileNotFoundError:
            error_message = ("I couldn't find git. The downloader needs it "
                             "to work properly.")
            if WINDOWS_OS:
                error_message += ("\nIf you just installed it, you may need "
                                  "a reboot for it to be seen in the PATH "
                                  "environment variable.")
            await self.bot.say(error_message)
            return False

        downloader.populate_list(repo_name)
        downloader.save_repos()
        return True

    async def do_cog_install(self, ctx, downloader, repo_name, cog_name):
        data = downloader.get_info_data(repo_name, cog_name)

        try:
            install_cog = await downloader.install(repo_name, cog_name, notify_reqs=True)
        except RequirementFail:
            await self.bot.say("The %s cog has requirements that I could not install. "
                               "Check the console for more information." % cog_name)
            return False

        if data is not None:
            install_msg = data.get("INSTALL_MSG", None)
            if install_msg:
                await self.bot.say(install_msg[:2000])

        if install_cog is False:
            await self.bot.say("Invalid cog. Installation aborted.")
            return False

        await self.bot.say("Installation of %s completed. Load it now? (yes/no)" % cog_name)
        answer = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        if answer and answer.content.lower() == "yes":
            await ctx.invoke(self.bot.get_cog('Owner').load, cog_name=cog_name)
        else:
            await self.bot.say("Ok then, you can load it with `{}load {}`".format(ctx.prefix, cog_name))

        return True


def setup(bot):
    bot.add_cog(Redportal(bot))
