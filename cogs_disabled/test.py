from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake import Guild, TextChannel
from disnake.ext import commands
from disnake.ui import Button, View
from tools.message_splitter import MessageSplitter
from tools.archivist.logger import Logger


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    @commands.slash_command()
    async def this(self, inter):
        pass

    @this.sub_command_group()
    async def new(self, inter):
        pass

    @new.sub_command()
    async def test(self, inter: ApplicationCommandInteraction):
        logger = Logger(
            self.__bot,
            log_group='Commande',
            interaction=inter,
            task_info='command.test.test'
        )
        await logger.log_start('youpi')

        await logger.log_success('youpa')



def setup(bot):
    bot.add_cog(TestClass(bot))
