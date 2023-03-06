from config.variables import constants
from disnake import AllowedMentions, Embed, Permissions
from disnake.abc import GuildChannel
from disnake.ext import commands
from tools.archivist.logger import Logger
from tools.text_managers import read_yaml, write_yaml
import os


class StickyMessage(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild = self.__bot.guilds[0]
        self.__settings_directory = constants.DIRECTORY_STICKY_MESSAGES
        self.__create_settings_directory()
        self.__settings = self.__read_settings()

    def __create_settings_directory(self) -> None:
        directory_split = self.__settings_directory.split('/')
        current_layer = []
        for layer in directory_split:
            current_layer.append(layer)
            try:
                os.mkdir('/'.join(current_layer))
            except:
                pass

    def __read_settings(self) -> list:
        output = []
        for file in self.__get_file_list():
            file_content = read_yaml(self.__settings_directory + file)
            output.append(file_content)
        return output

    def __get_file_list(self) -> list:
        try:
            files = os.listdir(self.__settings_directory)
            return [file for file in files if file[-4:] == '.yml']
        except:
            return []

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.__there_is_nothing_to_do(message):
            return

        logger = Logger(
            self.__bot,
            log_group='Tâche',
            message_success=f'Sticky message rafraîchi dans {message.channel.mention}.',
            task_info='task.sticky.update'
        )

        settings_list = self.__get_settings(message.channel.id)
        settings = settings_list[0]
        sticky_embed = self.__build_embed(settings)

        async for previous_message in message.channel.history(limit=10):
            if previous_message.author == self.__bot.user and previous_message.embeds[0] ==  sticky_embed:
                await previous_message.delete()

        await message.channel.send(embed=sticky_embed,
                                   allowed_mentions=AllowedMentions(everyone=False, users=False))

        await logger.log_success()
        return

    def __there_is_nothing_to_do(self, message) -> bool:
        if message.author == self.__bot.user:
            return True
        settings_list = self.__get_settings(message.channel.id)
        if not settings_list:
            return True
        return False

    def __get_settings(self, channel_id):
        return [settings for settings in self.__settings if channel_id in settings['channel_id']]

    @staticmethod
    def __build_embed(settings: dict) -> Embed:
        embed = Embed(
            title="" + settings["title"],
            description=settings["description"]
        )
        return embed

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_create(self, inter, name: str, message_id: str, title: str = '', channel: GuildChannel = None):
        """
        Crée un sticky à partir d'un message de ce canal.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la création du sticky "{name}".""",
            message_success=f"""Le sticky "{name}" a été créé.""",
            message_failure=f"""Le sticky "{name}" n'a pas été créé.""",
            task_info='command.sticky.create',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name in self.__get_file_list():
            await logger.log_message(f"""Un sticky nommé "{name}" existe déjà.""")
            await logger.log_failure()
            return

        try:
            message = await inter.channel.fetch_message(message_id)
            text = message.content
        except:
            await logger.log_message(
                f"""Le message dont l'id est {message_id} n'a pas été trouvé dans {inter.channel.mention}""")
            await logger.log_failure()
            return

        channel_id = channel.id if channel else None
        if channel_id and len(self.__get_settings(channel_id)) > 0:
            await logger.log_message(f"""{channel.mention} est déjà associé à un sticky.""")
            await logger.log_failure()
            return

        message_settings = {
            "name": name,
            "channel_id": [channel_id] if channel_id else [],
            "title": title,
            "description": text
        }
        file_path = self.__settings_directory + file_name
        write_yaml(message_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_edit(self, inter, name: str, message_id: str, title: str = ''):
        """
        Modifie un sticky.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la modification du sticky "{name}".""",
            message_success=f"""Le sticky "{name}" a été modifié.""",
            message_failure=f"""Le sticky "{name}" n'a pas été modifié.""",
            task_info='command.sticky.edit',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucun sticky nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        try:
            message = await inter.channel.fetch_message(message_id)
            text = message.content
        except:
            await logger.log_message(
                f"""Le message dont l'id est {message_id} n'a pas été trouvé dans {inter.channel.mention}""")
            return

        message_settings = [settings for settings in self.__settings if settings["name"] == name][0]
        message_settings["title"] = title
        message_settings["description"] = text

        file_path = self.__settings_directory + file_name
        write_yaml(message_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_channel_add(self, inter, name: str, channel: GuildChannel):
        """
        Associe un canal à un sticky.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé l'ajout du sticky "{name}" sur {channel.mention}.""",
            message_success=f"""Le sticky "{name}" a été ajouté à {channel.mention}.""",
            message_failure=f"""Le sticky "{name}" n'a pas été ajouté à {channel.mention}.""",
            task_info='command.sticky.channel add',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if not file_name in self.__get_file_list():
            await logger.log_message(f"""Aucun sticky nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        channel_id = channel.id
        if len(self.__get_settings(channel_id)) > 0:
            await logger.log_message(f"""{channel.mention} est déjà associé à un sticky.""")
            await logger.log_failure()
            return

        message_settings = [settings for settings in self.__settings if settings["name"] == name][0]
        message_settings["channel_id"].append(channel_id)

        file_path = self.__settings_directory + file_name
        write_yaml(message_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_channel_remove(self, inter, channel: GuildChannel):
        """
        Retire un canal du sticky auquel il est associé.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé le retrait du sticky sur {channel.mention}.""",
            message_success=f"""Le sticky de {channel.mention} a été retiré.""",
            task_info='command.sticky.channel remove',
            interaction=inter
        )
        await logger.log_start()

        channel_id = channel.id
        if len(self.__get_settings(channel_id)) > 0:
            message_settings = [settings for settings in self.__settings if channel_id in settings["channel_id"]][0]
            channel_list = message_settings["channel_id"]
            channel_list.pop(channel_list.index(channel_id))

            file_name = message_settings["name"] + '.yml'
            file_path = self.__settings_directory + file_name
            write_yaml(message_settings, file_path)

            self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_list(self, inter):
        """
        Liste tous les sticky existants et les channels associés.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la liste des stickies.""",
            message_success=f"""La liste des stickies a été affichée sur {inter.channel.mention}.""",
            message_failure=f"""La liste des stickies n'a pas été affichée.""",
            task_info='command.sticky.list',
            interaction=inter
        )
        await logger.log_start()

        if not self.__settings:
            await logger.log_message("Il n'existe aucun sticky pour l'instant.")
            await logger.log_failure()
            return

        text = "__**Liste des stickies**__"
        for settings in self.__settings:
            text += f"""\n{settings["name"]}"""
            for channel_id in settings["channel_id"]:
                try:
                    channel = await self.__guild.fetch_channel(channel_id)
                    text += f" {channel.mention}"
                except:
                    pass
        await inter.channel.send(text)

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_check(self, inter, name):
        """
        Affiche un sticky et les channels associés.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé l'affichage du sticky "{name}".""",
            message_success=f"""Le sticky "{name}" a été affiché sur {inter.channel.mention}.""",
            message_failure=f"""Le sticky "{name}" n'a pas été affiché.""",
            task_info='command.sticky.check',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if not file_name in self.__get_file_list():
            await logger.log_message(f"""Aucun sticky nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        settings = [settings for settings in self.__settings if settings["name"] == name][0]
        sticky_embed = self.__build_embed(settings)
        text = f"""__**Sticky "{name}"**__"""
        if settings["channel_id"]:
            text += "\nActif sur"
        for channel_id in settings["channel_id"]:
            try:
                channel = await self.__guild.fetch_channel(channel_id)
                text += f" {channel.mention}"
            except:
                pass
        await inter.channel.send(text, embed=sticky_embed,
                                 allowed_mentions=AllowedMentions(everyone=False, users=False))

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def sticky_delete(self, inter, name):
        """
        Supprime un sticky.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la suppresion du sticky "{name}".""",
            message_success=f"""Le sticky "{name}" a été supprimé.""",
            message_failure=f"""Le sticky "{name}" n'a pas été supprimé.""",
            task_info='command.sticky.delete',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        file_path = self.__settings_directory + file_name
        try:
            os.remove(file_path)
        except:
            await logger.log_message(f"""Aucun sticky nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        self.__settings = self.__read_settings()

        await logger.log_success()
        return


def setup(bot):
    bot.add_cog(StickyMessage(bot))
