from config.variables import constants
from disnake import AllowedMentions, Embed
from disnake.ext import commands
from tools.archivist.logger import Logger
from tools.text_managers import read_yaml
import os


class StickyMessage(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__settings_directory = constants.DIRECTORY_STICKY_MESSAGES
        self.__settings = self.__read_settings()

    def __read_settings(self) -> dict:
        output = []
        files = os.listdir(directory)
        for file in [file for file in files if file[-4:] == '.yml' and file != 'template.yml']:
            file_content = read_yaml(directory + file)
            output.append(file_content)
        return output

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

        async for previous_message in message.channel.history(limit=20):
            if previous_message.author == self.__bot.user:
                await previous_message.delete()

        settings_list = self.__get_settings(message.channel.id)
        settings = settings_list[0]
        sticky_body = settings['body']
        sticky_embed = self.__build_embed(settings)
        await message.channel.send(content=sticky_body, embed=sticky_embed,
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
        embed = None
        if settings["embed"]:
            embed_settings = settings["embed"]
            embed = Embed(
                title=embed_settings["title"],
                description=embed_settings["description"]
            )
        return embed

    @commands.slash_command()
    async def create_sticky_message(self, interaction, name: str, channel_ids: [int] = None, message: str = None,
                                    embed_title: str = None, embed_content: str = None):
        # check if name doesn't already exist
        # if yes, warn user, display current and new versions, ask if [keep, replace, rename new]
        message_settings = {
            channel_id: channel_ids
            body: message,
            embed: {
                title: embed_title,
                description: embed_content
            }
        }
        # Write file
        # Refresh settings
        # Display embed
        return

    @commands.slash_command()
    async def add_channel_to_sticky_message(self, interaction, name: str, channel_id: int = None):
        # Check if channel not already in antoher sticky message
        return

    @commands.slash_command()
    async def list_sticky_messages(self, interaction):
        return

    @commands.slash_command()
    async def list_channels_with_sticky_messages(self, interaction):
        return

    @commands.slash_command()
    async def delete_sticky_message(self, interaction, name):
        return

    @commands.slash_command()
    async def check_sticky_message(self, interaction, name):
        return


def setup(bot):
    bot.add_cog(StickyMessage(bot))
