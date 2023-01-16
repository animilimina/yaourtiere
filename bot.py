import disnake
from config import config
from disnake.ext.commands import InteractionBot
from tools.logger import Logger


class Yaourtiere(InteractionBot):
    def __init__(self):
        self.guild = config.discord_guild
        self.__intents = self.__set_intents()
        InteractionBot.__init__(self, test_guilds=[self.guild], intents=self.__intents)
        self.__cog_manager_name = 'cogs.cog_manager'
        self.__token = config.discord_bot_token
        self.__logger = None

    @staticmethod
    def __set_intents():
        intents = disnake.Intents.default()
        intents.members = True
        return intents

    def run_bot(self):
        self.run(self.__token)

    async def on_ready(self):
        self.__logger = Logger(self)
        await self.__logger.log("**========== LE BOT A REDÉMARRÉ ==========**")
        if self.__cog_manager_name not in self.extensions:
            self.load_extension('cogs.cog_manager')
        await self.__logger.log("__Les cogs suivants ont été chargés au lancement__")
        for extension in self.extensions:
            await self.__logger.log(extension.split('.')[-1])


Yaourtiere().run_bot()
