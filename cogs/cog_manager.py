import disnake
import os
from disnake.ext import commands
from tools.authorisations import AuthorisationManager
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter


class CogManager(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__this_cog = os.path.basename(__file__).split('.')[0]
        self.__logger = None
        self.__cog_directory = 'cogs'
        self.__cog_list = []
        self.__current_cog = ''
        self.__cogs_unloaded = []
        self.__cogs_loaded = []
        self.__cogs_reloaded = []
        self.__interaction = None
        self.__authorisation_manager = None
        self.__initial_load()

    def __initial_load(self):
        if not list(self.__bot.extensions):
            self.__refresh_cog_list()
            self.__load_all_cogs()

    def __refresh_cog_list(self):
        cog_dir = self.__cog_directory
        self.__cog_list = [x.split('.')[0] for x in os.listdir(cog_dir) if os.path.isfile(f'{cog_dir}/{x}')]

    def __load_all_cogs(self):
        self.__cogs_loaded = []
        for cog in self.__cog_list:
            self.__current_cog = cog
            self.__load_cog()

    def __load_cog(self):
        if self.__current_cog != self.__this_cog:
            self.__bot.load_extension(self.__cog_directory + '.' + self.__current_cog)
            self.__cogs_loaded.append(self.__current_cog)

    @commands.slash_command(description="Réservé aux admins. Recharge les cogs (sauf le cog manager).")
    async def reload_all_cogs(self, inter):
        self.__logger = Logger(
            self.__bot,
            log_group='Commande ',
            message_start=f'{inter.author.mention} a demandé le rechargement des cogs.',
            message_success=f'Rechargement des cogs terminé.',
            interaction=inter,
            task_info='command.bot.reload cogs'
        )
        await self.__logger.log_start()
        if not await self.__logger.interaction_is_authorized('bot_admin'):
            return

        self.__unload_all_cogs()
        self.__refresh_cog_list()
        self.__load_all_cogs()
        self.__classify_cogs_unloaded_reloaded_loaded()
        await self.__log_cogs_unloaded_reloaded_loaded()

        await self.__logger.log_success()

    def __set_interaction(self, interaction):
        self.__interaction = interaction
        self.__authorisation_manager = AuthorisationManager(self.__interaction)

    def __unload_all_cogs(self):
        self.__cogs_unloaded = []
        for extension in list(self.__bot.extensions):
            self.__current_cog = extension.split('.')[-1]
            self.__unload_cog()

    def __unload_cog(self):
        if self.__current_cog != self.__this_cog:
            self.__bot.unload_extension(self.__cog_directory + '.' + self.__current_cog)
            self.__cogs_unloaded.append(self.__current_cog)

    def __classify_cogs_unloaded_reloaded_loaded(self):
        self.__cogs_reloaded = [cog for cog in self.__cogs_unloaded if cog in self.__cogs_loaded]
        self.__cogs_unloaded = [cog for cog in self.__cogs_unloaded if cog not in self.__cogs_reloaded]
        self.__cogs_loaded = [cog for cog in self.__cogs_loaded if cog not in self.__cogs_reloaded]

    async def __log_cogs_unloaded_reloaded_loaded(self):
        message_full = ''
        if self.__cogs_unloaded:
            message_full += "\n__Les cogs suivants ont été déchargés__```\n" + "\n".join(self.__cogs_unloaded) + "```"
        if self.__cogs_reloaded:
            message_full += "\n__Les cogs suivants ont été rechargés__```\n" + "\n".join(self.__cogs_reloaded) + "```"
        if self.__cogs_loaded:
            message_full += "\n__Les cogs suivants ont été chargés__```\n" + "\n".join(self.__cogs_loaded) + "```"
        if not self.__cogs_loaded and not self.__cogs_reloaded and not self.__cogs_unloaded:
            await self.__logger.log_message("Aucun cog n'a été affecté par l'action")
        else:
            message_split = MessageSplitter(message_full).get_message_split()
            for message in message_split:
                await self.__logger.log_message(message)

    @commands.slash_command(description="Réservé aux admins. Recharge le cog manager.")
    async def reload_cog_manager(self, inter):
        self.__logger = Logger(
            self.__bot,
            log_group='Commande ',
            message_start=f'{inter.author.mention} a demandé le rechargement du cog manager.',
            message_success=f'Rechargement du cog manager terminé.',
            interaction=inter,
            task_info='command.bot.reload cog manager'
        )
        await self.__logger.log_start()
        if not await self.__logger.interaction_is_authorized('bot_admin'):
            return

        cog_manager = 'cogs.' + self.__this_cog
        self.__bot.unload_extension(cog_manager)
        self.__bot.load_extension(cog_manager)

        await self.__logger.log_success()


def setup(bot):
    bot.add_cog(CogManager(bot))
