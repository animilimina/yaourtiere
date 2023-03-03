from config.variables import constants
from disnake import AllowedMentions, Embed
from disnake.ext import commands
from tools.archivist.logger import Logger
from tools.text_managers import read_yaml, write_yaml
import os


class StickyMessage(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__settings_directory = constants.DIRECTORY_STICKY_MESSAGES
        self.__settings = self.__read_settings()

    def __read_settings(self) -> dict:
        output = []
        for file in self.__get_file_list():
            file_content = read_yaml(self.__settings_directory + file)
            output.append(file_content)
        return output

    def __get_file_list(self) -> list:
        files = os.listdir(self.__settings_directory)
        return [file for file in files if file[-4:] == '.yml' and file != 'template.yml']

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.__there_is_nothing_to_do(message):
            return

        logger = Logger(
            self.__bot,
            log_group='Tâche automatisée ',
            message_success=f'Sticky message rafraîchi dans {message.channel.mention}.',
            task_info='task.update.sticky message'
        )

        async for previous_message in message.channel.history(limit=10):
            if previous_message.author == self.__bot.user:
                await previous_message.delete()

        settings_list = self.__get_settings(message.channel.id)
        settings = settings_list[0]
        sticky_embed = self.__build_embed(settings)
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
            title=settings["title"],
            description=settings["description"]
        )
        return embed

    @commands.slash_command()
    async def sticky_create(self, inter, message_id: str, name: str,
                                    title: str = '', channel_id: str = ''):
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} a demandé la création d'un _sticky message_ "{name}".""",
            message_success=f"""Le _sticky message_ "{name}" de {inter.author.mention} a été créé.""",
            message_failure=f"""Le _sticky message_ "{name}" de {inter.author.mention} n'a pas pu être créé.""",
            task_info='command.create.sticky message',
            interaction=inter
        )
        await logger.log_start()
        if not await logger.interaction_is_authorized('bot_admin'):
            return

        file_name = name + '.yml'
        if file_name in self.__get_file_list():
            await logger.log_failure()
            return

        try:
            message = await inter.channel.fetch_message(message_id)
            text = message.content
            channel_id = int(channel_id)
        except:
            await logger.log_failure()
            return

        if len(self.__get_settings(channel_id)) > 0:
            await logger.log_failure()
            return

        message_settings = {
            "channel_id": [channel_id] if channel_id else [],
            "title": title,
            "description": text
        }
        file_path = self.__settings_directory + file_name
        write_yaml(message_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command()
    async def sticky_channel_add(self, interaction, name: str, channel_id: int = None):
        # Check if channel not already in antoher sticky message
        return

    @commands.slash_command()
    async def sticky_channel_remove(self, interaction, name: str, channel_id: int = None):
        # Check if channel not already in antoher sticky message
        return

    @commands.slash_command()
    async def sticky_list_messages(self, interaction):
        return

    @commands.slash_command()
    async def sticky_list_channels(self, interaction):
        return

    @commands.slash_command()
    async def sticky_delete(self, interaction, name):
        return

    @commands.slash_command()
    async def sticky_check(self, interaction, name):
        return


def setup(bot):
    bot.add_cog(StickyMessage(bot))


def a(a: int, b: int, *c: str):
    print(list(c))
