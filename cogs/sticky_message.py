from config import config
from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake import AllowedMentions, Embed
from disnake.ext import commands, tasks
from tools.archivist.logger import Logger
from tools.text_importers import read_yaml
import os


class StickyMessage(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__settings = self.__read_settings()

    def __read_settings(self) -> dict:
        output = []
        directory = 'config/sticky_messages/'
        files = os.listdir(directory)
        for file in [file for file in files if file[-4:] == '.yml' and file != 'template.yml']:
            file_content = read_yaml(directory + file)
            output.append(file_content)
        return output

    @commands.slash_command()
    async def create_sticky_message(self, interaction, name: str, channel_id: int, title: str, content: str):
        return

    @commands.slash_command()
    async def add_channel_to_sticky_message(self, interaction, name: str, channel_id: int = None):
        return

    @commands.slash_command()
    async def list_sticky_messages(self, interaction):
        return

    @commands.slash_command()
    async def delete_sticky_message(self, interaction, name):
        return

    @commands.slash_command()
    async def check_sticky_message(self, interaction, name):
        return

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
        sticky_embed = None
        if settings["embed"]:
            sticky_embed = Embed(
                title=settings["embed"]["title"],
                description=settings["embed"]["description"]
            )
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


def setup(bot):
    bot.add_cog(StickyMessage(bot))
