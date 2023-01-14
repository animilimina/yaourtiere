from disnake.ext import commands
from tools.archivist.logger import Logger
from tools.authorisations import AuthorisationManager


class ActionManager:
    def __init__(self, bot, interaction):
        self.__bot = bot
        self.__interaction = interaction
        self.__authorisation_manager = AuthorisationManager(self.__interaction)
        self.__logger = None

    async def do_something(self):
        self.__logger = Logger(bot=self.__bot,
                               log_group='Test',
                               message_start="${user} a utilisé une commande",
                               message_success="la commande de ${user} est un succès",
                               interaction=self.__interaction)
        await self.__logger.log_start()
        if not self.__authorisation_manager.interaction_user_is_in_group('bot_admin'):
            await self.__logger.log_rejection()
            return
        await self.__logger.log_message("Test du message splitter.\nTexte relativement court.\nMais un peu long quand même...")
        await self.__logger.log_success()


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test_command(self, interaction):
        action = ActionManager(self.__bot, interaction)
        await action.do_something()


def setup(bot):
    bot.add_cog(TestClass(bot))
