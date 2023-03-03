import disnake
from config import config
from disnake.ext.commands import InteractionBot
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter


class Yaourtiere(InteractionBot):
    def __init__(self):
        self.guild = config.discord_guild
        self.__intents = self.__set_intents()
        InteractionBot.__init__(self, test_guilds=[self.guild], intents=self.__intents)
        self.__cog_manager_name = 'cogs.cog_manager'
        self.__token = config.discord_bot_token

    @staticmethod
    def __set_intents():
        intents = disnake.Intents.default()
        intents.members = True
        return intents

    def run_bot(self):
        self.run(self.__token)

    async def on_ready(self):
        logger = Logger(
            self,
            message_start="**========== LE BOT A REDÉMARRÉ ==========**",
            task_info='task.bot.start'
        )
        await logger.log_start()
        if self.__cog_manager_name not in self.extensions:
            self.load_extension('cogs.cog_manager')
        message_full = "__Les cogs suivants ont été chargés au lancement__```\n" + "\n".join(
            [extension.split('.')[-1] for extension in self.extensions]) + "```"
        message_split = MessageSplitter(message_full).get_message_split()
        for message in message_split:
            await logger.log_message(message)


Yaourtiere().run_bot()
