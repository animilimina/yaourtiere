from config.variables import constants
from disnake import AllowedMentions, Embed, Permissions
from disnake.abc import GuildChannel
from disnake.ext import commands, tasks
from tools.archivist.logger import Logger
from tools.text_managers import read_yaml, write_yaml
import os


class TestCollector(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild = self.__bot.guilds[0]
        self.__settings_directory = constants.DIRECTORY_TEST_COLLECTOR
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

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_create(self, inter, name: str, new: str, correct: str, hint: str = None, close: str = None,
                               wrong: str = None, yes: str = None, no: str = None, channel: GuildChannel = None):
        """
        Crée un collecteur.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la création du collecteur "{name}".""",
            message_success=f"""Le collecteur "{name}" a été créé.""",
            message_failure=f"""Le collecteur "{name}" n'a pas été créé.""",
            task_info='command.collector.create',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name in self.__get_file_list():
            await logger.log_message(f"""Un collecteur nommé "{name}" existe déjà.""")
            await logger.log_failure()
            return

        channel_id = channel.id if channel else None
        if channel_id and len(self.__get_settings_for_channel(channel_id)) > 0:
            await logger.log_message(f"""{channel.mention} est déjà associé à un collecteur.""")
            await logger.log_failure()
            return
        channel_dict = None
        if channel_id:
            channel_dict = {
                "channel_id": channel_id,
                "last_message_id": 0
            }

        collector_settings = {
            "name": name,
            "channel": [channel_dict] if channel_dict else [],
            "games": 0,
            "rules": {
                "new": new.split(' '),
                "correct": correct.split(' ')
            }
        }
        if hint:
            collector_settings["rules"]["hint"] = hint.split(' ')
        if close:
            collector_settings["rules"]["close"] = close.split(' ')
        if wrong:
            collector_settings["rules"]["wrong"] = wrong.split(' ')
        if yes:
            collector_settings["rules"]["yes"] = yes.split(' ')
        if no:
            collector_settings["rules"]["no"] = no.split(' ')

        file_path = self.__settings_directory + file_name
        write_yaml(collector_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_edit(self, inter, name: str, new: str, correct: str, hint: str = None, close: str = None,
                             wrong: str = None, yes: str = None, no: str = None):
        """
        Modifie un collecteur.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la modification du collecteur "{name}".""",
            message_success=f"""Le collecteur "{name}" a été modifié.""",
            message_failure=f"""Le collecteur "{name}" n'a pas été modifié.""",
            task_info='command.collector.edit',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucun collecteur nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        collector_settings = [settings for settings in self.__settings if settings["name"] == name][0]

        collector_settings["rules"]["new"] = new.split(' ')
        collector_settings["rules"]["correct"] = correct.split(' ')

        if hint:
            collector_settings["rules"]["hint"] = hint.split(' ')
        else:
            collector_settings["rules"].pop("hint")

        if close:
            collector_settings["rules"]["close"] = close.split(' ')
        else:
            collector_settings["rules"].pop("close")

        if wrong:
            collector_settings["rules"]["wrong"] = wrong.split(' ')
        else:
            collector_settings["rules"].pop("wrong")

        if yes:
            collector_settings["rules"]["yes"] = yes.split(' ')
        else:
            collector_settings["rules"].pop("yes")

        if no:
            collector_settings["rules"]["no"] = no.split(' ')
        else:
            collector_settings["rules"].pop("no")

        file_path = self.__settings_directory + file_name
        write_yaml(collector_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    def __get_settings_for_channel(self, channel_id):
        output = []
        for settings in self.__settings:
            channels = settings["channel"]
            if channel_id in [channel["channel_id"] for channel in channels]:
                output.append(settings)
        return output

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_channel_add(self, inter, name: str, channel: GuildChannel):
        """
        Ajoute un canal à un collecteur.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé l'ajout de {channel.mention} au collecteur "{name}".""",
            message_success=f"""{channel.mention} a été ajouté au collecteur "{name}".""",
            message_failure=f"""{channel.mention} n'a pas été ajouté au collecteur "{name}".""",
            task_info='command.collector.channel add',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if not file_name in self.__get_file_list():
            await logger.log_message(f"""Aucun collecteur nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return
        channel_id = channel.id
        if channel_id and len(self.__get_settings_for_channel(channel_id)) > 0:
            await logger.log_message(f"""{channel.mention} est déjà associé à un collecteur.""")
            await logger.log_failure()
            return
        channel_dict = {
            "channel_id": channel_id,
            "last_message_id": 0
        }
        collector_settings = [settings for settings in self.__settings if settings["name"] == name][0]
        collector_settings["channel"].append(channel_dict)

        file_path = self.__settings_directory + file_name
        write_yaml(collector_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_channel_remove(self, inter, channel: GuildChannel):
        """
        Retire un canal du collector auquel il est associé.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé le retrait de {channel.mention} de son collector.""",
            message_success=f"""{channel.mention} a été retiré de son collector.""",
            task_info='command.collector.channel remove',
            interaction=inter
        )
        await logger.log_start()

        channel_id = channel.id
        if len(self.__get_settings_from_channel(channel_id)) > 0:
            message_settings = [settings for settings in self.__settings if channel_id in settings["channel_id"]][0]
            channel_list = message_settings["channel_id"]
            channel_list.pop(channel_list.index(channel_id))

            file_name = message_settings["name"] + '.yml'
            file_path = self.__settings_directory + file_name
            write_yaml(message_settings, file_path)

            self.__settings = self.__read_settings()

        await logger.log_success()
        return


    @commands.slash_command()
    async def test_collector_initialise(self, inter):
        # If db item exists -> pass
        # Create db thread item
        # Collect test history
        # Set db thread item to active
        pass

    @commands.slash_command()
    async def test_collector_pause(self, inter):
        # If db item does not exist -> pass
        # If already paused -> pass
        # Set deb thread item to inactive
        pass

    @commands.slash_command()
    async def test_collector_resume(self, inter):
        # If db item does not exist -> pass
        # If not paused -> pass
        # Collect test history
        # Set db thread item to active
        pass

    @tasks.loop(hours=3)
    async def collect_recent_tests(self, inter):
        # Collect test history
        pass

    # History collector
    # Get last message collected -> thread item
    # Loop through messages since then
    # Only store full tests? -> No we can use a current test item
    # For each test, increase counter for game master and winner


# Tester si on peut ajouter plusieurs cogs à la fois dans la fonction

def setup(bot):
    bot.add_cog(TestCollector(bot))
