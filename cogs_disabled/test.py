from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake import Guild, TextChannel
from disnake.ext import commands
from disnake.ui import Button, View
from tools.message_splitter import MessageSplitter


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    @commands.slash_command()
    async def haut(self, inter):
        return

    @haut.autocomplete("text")
    async def autocomplete(self, inter: ApplicationCommandInteraction, user_input: str):
        string = user_input.lower()
        mylist = ['bonjour', 'bonsoir', 'salut', 'sabord', 'bonbon', 'bretagne', 'baleine', 'ballon', 'bal masqué']
        return [x for x in mylist if string in x]

    @haut.sub_command_group()
    async def a(self, inter):
        return

    @haut.sub_command_group()
    async def b(self, inter):
        return

    @a.sub_command()
    async def bas(self, inter, text: str):
        await inter.response.send_message('a: ' + text)

    @b.sub_command()
    async def bas(self, inter, text: str):
        await inter.response.send_message('b: ' + text)


def setup(bot):
    bot.add_cog(TestClass(bot))
