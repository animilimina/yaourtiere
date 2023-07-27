from config.variables import constants
from datetime import datetime
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

    # @tasks.loop(hours=1)
    @commands.slash_command()
    async def collect_new_tests(self, inter):
        """
        Collecte les nouveaux tests.
        """
        # if datetime.now().hour != 4:
        #     return

        logger = Logger(
            self.__bot,
            log_group='Tâche',
            message_start=f"""Début de la collecte des tests.""",
            message_success=f"""Collecte des tests terminée.""",
            task_info='task.collector.collect',
            interaction=inter
        )
        await logger.log_start()

        for test_settings in self.__settings:

            file_name = test_settings["name"] + '.yml'
            file_path = self.__settings_directory + file_name

            for channel_dict in test_settings["channel"]:

                channel_id = channel_dict["channel_id"]
                channel = self.__guild.fetch_channel(channel_id)

                last_message_id = channel_dict["last_message_id"]
                last_message = channel.fetch_message(last_message_id)

                test_info = {}
                rules = test_settings["rules"]
                async for message in channel.history(limit=None, after=last_message, oldest_first=True):
                    reactions = message.reactions
                    for reaction in reactions:
                        if reaction in rules["new"]:
                            test_settings["games"] += 1
                            # write item
                            test_info = {"question": {
                                "content": message.content,
                                "attachments": [attachment.url for attachment in message.attachments]
                            }}





            # write_yaml(collector_settings, file_path)



        # channel_dict = None
        # if channel_id:
        #     channel_dict = {
        #         "channel_id": channel_id,
        #         "last_message_id": 0
        #     }
        #
        # collector_settings = {
        #     "name": name,
        #     "channel": [channel_dict] if channel_dict else [],
        #     "games": 0,
        #     "rules": {
        #         "new": new.split(' '),
        #         "correct": correct.split(' ')
        #     }
        # }
        # if hint:
        #     collector_settings["rules"]["hint"] = hint.split(' ')
        # if close:
        #     collector_settings["rules"]["close"] = close.split(' ')
        # if wrong:
        #     collector_settings["rules"]["wrong"] = wrong.split(' ')
        # if yes:
        #     collector_settings["rules"]["yes"] = yes.split(' ')
        # if no:
        #     collector_settings["rules"]["no"] = no.split(' ')
        #
        # file_path = self.__settings_directory + file_name
        # write_yaml(collector_settings, file_path)
        #
        # self.__settings = self.__read_settings()

        await logger.log_success()
        return


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
        Retire un canal du collecteur auquel il est associé.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé le retrait de {channel.mention} de son collecteur.""",
            message_success=f"""{channel.mention} a été retiré de son collecteur.""",
            task_info='command.collector.channel remove',
            interaction=inter
        )
        await logger.log_start()

        channel_id = channel.id
        settings_list = self.__get_settings_for_channel(channel_id)
        if len(settings_list) > 0:
            collector_settings = settings_list[0]
            channels = collector_settings["channel"]
            channel_to_remove = [channel for channel in channels if channel["channel_id"] == channel_id][0]
            channels.pop(channels.index(channel_to_remove))

            file_name = collector_settings["name"] + '.yml'
            file_path = self.__settings_directory + file_name
            write_yaml(collector_settings, file_path)

            self.__settings = self.__read_settings()

        await logger.log_success()
        return


    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_list(self, inter):
        """
        Liste tous les collecteurs existants et les canaux associés.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la liste des collecteurs.""",
            message_success=f"""La liste des collecteurs a été affichée sur {inter.channel.mention}.""",
            message_failure=f"""La liste des collecteurs n'a pas été affichée.""",
            task_info='command.collector.list',
            interaction=inter
        )
        await logger.log_start()

        if not self.__settings:
            await logger.log_message("Il n'existe aucun collecteur pour l'instant.")
            await logger.log_failure()
            return

        text = "__**Liste des collecteurs**__"
        for settings in self.__settings:
            text += f"""\n{settings["name"]}"""
            for channel_id in [channel["channel_id"] for channel in settings["channel"]]:
                try:
                    channel = await self.__guild.fetch_channel(channel_id)
                    text += f" {channel.mention}"
                except:
                    pass
        await inter.channel.send(text)

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_check(self, inter, name):
        """
        Affiche les informations sur collecteur.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé les informations sur le collecteur "{name}".""",
            message_success=f"""Les informations sur le collecteur "{name}" ont été affichées sur {inter.channel.mention}.""",
            message_failure=f"""Les informations sur le collecteur "{name}" n'ont pas été affichées.""",
            task_info='command.collector.check',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        if not file_name in self.__get_file_list():
            await logger.log_message(f"""Aucun collecteur nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

        settings = [settings for settings in self.__settings if settings["name"] == name][0]
        text = f"""__**Collecteur "{name}"**__"""
        if settings["channel"]:
            text += "\nActif sur"
        for channel_id in [channel["channel_id"] for channel in settings["channel"]]:
            try:
                channel = await self.__guild.fetch_channel(channel_id)
                text += f" {channel.mention}"
            except:
                pass
        rules = settings["rules"]
        embed_description = "Nouvelle question : " + (" ".join(rules["new"]))
        embed_description += "\nBonne réponse : " + (" ".join(rules["correct"]))
        if "hint" in rules.keys():
            embed_description += "\nIndice : " + (" ".join(rules["hint"]))
        if "close" in rules.keys():
            embed_description += "\nPresque : " + (" ".join(rules["close"]))
        if "wrong" in rules.keys():
            embed_description += "\nMauvaise réponse : " + (" ".join(rules["wrong"]))
        if "yes" in rules.keys():
            embed_description += "\nOui : " + (" ".join(rules["yes"]))
        if "no" in rules.keys():
            embed_description += "\nNon : " + (" ".join(rules["no"]))
        embed = Embed(description=embed_description)
        await inter.channel.send(text, embed=embed,
                                 allowed_mentions=AllowedMentions(everyone=False, users=False))

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def collector_delete(self, inter, name):
        """
        Supprime un sticky.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la suppresion du collecteur "{name}".""",
            message_success=f"""Le collecteur "{name}" a été supprimé.""",
            message_failure=f"""Le collecteur "{name}" n'a pas été supprimé.""",
            task_info='command.collector.delete',
            interaction=inter
        )
        await logger.log_start()

        file_name = name + '.yml'
        file_path = self.__settings_directory + file_name
        try:
            os.remove(file_path)
        except:
            await logger.log_message(f"""Aucun collecteur nommé "{name}" n'a été trouvé.""")
            await logger.log_failure()
            return

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
