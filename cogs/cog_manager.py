import disnake
import os
from disnake.ext import commands
from tools.authorisations import AuthorisationManager
from tools.logger import Logger


class CogManager(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__logger = Logger(self.__bot)
        self.__this_cog = os.path.basename(__file__).split('.')[0]
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
        self.__set_interaction(inter)
        await self.__interaction.response.defer()
        await self.__logger.log(self.__interaction.author.mention + " a demandé rechargement des cogs.")
        if not self.__authorisation_manager.interaction_user_is_in_group('bot_admin'):
            await self.__authorisation_manager.reject_interaction()
            return
        self.__unload_all_cogs()
        self.__refresh_cog_list()
        self.__load_all_cogs()
        self.__classify_cogs_unloaded_reloaded_loaded()
        await self.__log_cogs_unloaded_reloaded_loaded()
        await self.__interaction.edit_original_response("La recharge des cogs est terminée.")
        await self.__interaction.delete_original_response(delay=2)

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
        if self.__cogs_unloaded:
            await self.__log_cogs_unloaded()
        if self.__cogs_reloaded:
            await self.__log_cogs_reloaded()
        if self.__cogs_loaded:
            await self.__log_cogs_loaded()
        if not self.__cogs_loaded and not self.__cogs_reloaded and not self.__cogs_unloaded:
            await self.__logger.log("Aucun cog n'a été affecté par l'action")

    async def __log_cogs_unloaded(self):
        await self.__logger.log("__Les cogs suivants ont été déchargés__")
        for cog in self.__cogs_unloaded:
            await self.__logger.log(cog)

    async def __log_cogs_reloaded(self):
        await self.__logger.log("__Les cogs suivants ont été rechargés__")
        for cog in self.__cogs_reloaded:
            await self.__logger.log(cog)

    async def __log_cogs_loaded(self):
        await self.__logger.log("__Les cogs suivants ont été chargés__")
        for cog in self.__cogs_loaded:
            await self.__logger.log(cog)

    @commands.slash_command(description="Réservé aux admins. Recharge le cog manager.")
    async def reload_cog_manager(self, inter):
        self.__set_interaction(inter)
        await self.__interaction.response.defer()
        await self.__logger.log(self.__interaction.author.mention + " a demandé un rechargement du cog manager.")
        if not self.__authorisation_manager.interaction_user_is_in_group('bot_admin'):
            await self.__authorisation_manager.reject_interaction()
            return
        cog_manager = 'cogs.' + self.__this_cog
        self.__bot.unload_extension(cog_manager)
        self.__bot.load_extension(cog_manager)
        await self.__logger.log("Le cog manager a été rechargé.")
        await self.__interaction.edit_original_response("Le cog manager a été rechargé.")
        await self.__interaction.delete_original_response(delay=2)


def setup(bot):
    bot.add_cog(CogManager(bot))
