from config.variables import constants
from disnake import ApplicationCommandInteraction, Embed, Guild, Permissions, ApplicationCommandInteraction, Message, \
    TextChannel
from disnake.abc import GuildChannel
from disnake.ext import commands
from disnake.ui import Button, View
import os
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_yaml, write_yaml


class Search(commands.Cog):
    def __init__(self, bot) -> None:
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings_directory: str = constants.DIRECTORY_SEARCH
        self.__settings: dict = {}
        self.__read_settings()

    def __read_settings(self) -> None:
        for file in self.__get_file_list():
            self.__settings[file[:-4]] = read_yaml(self.__settings_directory + file)

    def __get_file_list(self) -> list:
        try:
            files = os.listdir(self.__settings_directory)
            return [file for file in files if file[-4:] == '.yml']
        except:
            return []

    @commands.slash_command()
    async def search(self, interaction: ApplicationCommandInteraction) -> None:
        pass

    @search.sub_command()
    async def thread(self, interaction: ApplicationCommandInteraction, expression: str) -> None:
        """
        Recherche un canal dont le titre contient les mots indiqués

        Parameters
        ----------
        expression: :class: str
            Le texte à rechercher.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.search.thread',
            interaction=interaction
        )

        await logger.log_start(f"""{interaction.author.mention} cherche un fil contenant "**{expression}**".""")

        user = interaction.author

        result_channel = interaction.channel
        self.__check_settings_existence('thread')
        if "channel_id" in self.__settings["thread"].keys():
            try:
                result_channel = await self.__guild.fetch_channel(self.__settings["thread"]["channel_id"])
            finally:
                pass

        channels = await self.__guild.fetch_channels()
        active_threads = await self.__guild.active_threads()

        all_threads = []

        for channel in channels:
            all_threads.extend([x for x in active_threads if x.parent == channel])
            if isinstance(channel, TextChannel):
                try:
                    async for thread in channel.archived_threads(limit=None):
                        all_threads.append(thread)
                except:
                    pass
                finally:
                    pass

        filtered_list = [x for x in all_threads if expression.lower() in x.name.lower()]

        if len(filtered_list) == 0:
            message = f"""{user.mention} désolé, pas de résultat pour "**{expression}**". À toi de créer ce fil ;-)"""
            result = await result_channel.send(message)
            await logger.log_success(
                f"La recherche de fil de {user.mention} n'a pas donné de résultat. {result.jump_url}")
            temporary_message = await interaction.channel.send(f"Pas de résultat : {result.jump_url}")
        else:
            message = f"""{user.mention} tu trouveras "**{expression}**" dans :"""
            embed_text = '\n'.join([f"""{x.parent.name} > [#{x.name}]({x.jump_url})""" for x in filtered_list])
            embed_text_splitter = MessageSplitter(embed_text)
            texts = embed_text_splitter.get_message_split()

            result = await result_channel.send(message, embed=Embed(description=texts[0]))
            texts = texts[1:]
            while texts:
                await result_channel.send(embed=Embed(description=texts[0]))
                texts = texts[1:]
            await logger.log_success(f"La recherche de fil de {user.mention} a abouti. {result.jump_url}")
            temporary_message = await interaction.channel.send(f"Tes résultats sont ici : {result.jump_url}")

        await temporary_message.delete(delay=5)
        return

    def __check_settings_existence(self, name: str):
        if name not in self.__settings.keys():
            self.__settings[name] = {}

    @commands.slash_command()
    @commands.default_member_permissions(moderate_members=True)
    async def search_admin_thread(self, interaction: ApplicationCommandInteraction, channel: GuildChannel) -> None:
        """
        Définit le canal utilisé pour les recherches de fil

        Parameters
        ----------
        channel: :class: GuildChannel
            Le salon ou fil où seront affichés les résultats.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} souhaite définir {channel.mention} pour les recherches de fils.""",
            message_success=f"""{channel.mention} est à présent utilisé pour les recherches de fils.""",
            task_info='command.search.set',
            interaction=interaction
        )

        await logger.log_start()

        self.__check_settings_existence('thread')

        self.__settings["thread"]["channel_id"] = channel.id
        file_path = self.__settings_directory + 'thread.yml'
        write_yaml(self.__settings["thread"], file_path)

        await logger.log_success()
        return


def setup(bot):
    bot.add_cog(Search(bot))
