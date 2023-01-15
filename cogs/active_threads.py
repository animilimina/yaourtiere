from config import config
from datetime import datetime, timedelta, timezone
from disnake.ext import commands, tasks
from tools.archivist.logger import Logger
from tools.text_importers import read_yaml


class ActiveThreads(commands.Cog):

    """
    Builds and publishes list of currently active threads on the server
    """

    def __init__(self, bot):
        self.__bot = bot
        self.__guild = self.__bot.guilds[0]
        self.__settings = self.__read_settings()
        self.__channel_to_update = self.__bot.get_channel(self.__settings["channel"][config.working_environment])
        self.__date = datetime.now(tz=timezone.utc)
        self.__channel_threads = []
        self.__messages = ['']
        self.refresh_open_threads_list.start()

    @staticmethod
    def __read_settings():
        return read_yaml('config/active_threads.yml')

    def __initialize_run(self) -> None:

        """
        Resets settings and date.
        """

        self.__date = datetime.now(tz=timezone.utc)
        self.__settings = self.__read_settings()

    @tasks.loop(hours=1)
    async def refresh_open_threads_list(self) -> None:

        """
        Extracts open threads list, builds messages and posts them.
        """

        logger = Logger(
            self.__bot,
            log_group='Tâche automatisée',
            message_start=f'Mise à jour du salon {self.__channel_to_update.mention}.',
            message_success=f'Mise à jour du salon {self.__channel_to_update.mention} terminée.',
            task_info='task.update.active threads'
        )

        await logger.log_start()

        self.__initialize_run()
        await self.__build_channel_thread_list()
        self.__build_messages()
        await self.__clean_channel()
        await self.__update_channel()

        await logger.log_success()
        return

    async def __build_channel_thread_list(self) -> None:

        """
        Clears and re-populates the __channel_threads property.
        """

        self.__channel_threads = []
        threads = await self.__guild.active_threads()

        while threads:
            channel = threads[0].parent
            threads_channel = [thread for thread in threads if thread.parent == channel]

            channel_dictionary = {
                "channel": channel,
                "threads": [thread for thread in threads_channel if not self.__thread_is_dead(thread)]
            }
            if len(channel_dictionary["threads"]) > 0:
                self.__channel_threads.append(channel_dictionary)

            for thread in threads_channel:
                threads.remove(thread)

    def __thread_is_dead(self, thread):
        archive_date = self.__get_archive_date(thread)
        return archive_date < datetime.now(tz=timezone.utc)

    @staticmethod
    def __get_archive_date(thread) -> datetime:
        up_timestamp = thread.archive_timestamp
        try:
            last_message = thread.last_message.created_at
        except:
            last_message = up_timestamp
        last_activity = last_message if last_message > up_timestamp else up_timestamp
        return last_activity + timedelta(minutes=thread.auto_archive_duration)

    def __build_messages(self) -> None:

        """
        Builds a list of messages to post in the Open Threads channel
        """

        self.__messages = ['']
        for channel in self.__channel_threads:
            self.__complete_last_message('\n\n\n')
            self.__complete_last_message(channel["channel"].mention)

            for thread in channel["threads"]:
                thread_string = f"\n> {thread.mention}"
                thread_string += self.__check_if_new(thread)
                thread_string += self.__check_if_up(thread)
                thread_string += self.__check_if_dying(thread)
                self.__complete_last_message(thread_string)

        return

    def __complete_last_message(self, string_to_add) -> None:

        """
        Adds the string to the last item of the __messages property if it doesn't exceed the character limit.
        Otherwise, appends this string to the list.

        :param string_to_add: The string to add to the last message
        """

        message_length = len(self.__messages[-1])
        string_length = len(string_to_add)

        if message_length + string_length <= self.__settings["message_length"]:
            self.__messages[-1] += string_to_add
        else:
            self.__messages.append(string_to_add)

        return


    def __check_if_new(self, thread) -> str:
        parameters = self.__settings["new"]
        hours_since_creation = (self.__date - thread.create_timestamp).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_since_creation < hours_for_emoji else ''
        return output

    def __check_if_up(self, thread) -> str:
        parameters = self.__settings["up"]
        not_new = thread.archive_timestamp > thread.create_timestamp
        hours_since_up = (self.__date - thread.archive_timestamp).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_since_up < hours_for_emoji and not_new else ''
        return output

    def __check_if_dying(self, thread) -> str:
        parameters = self.__settings["dying"]
        archive_date = self.__get_archive_date(thread)
        hours_until_archive = (archive_date - self.__date).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_until_archive < hours_for_emoji else ''
        return output


    async def __clean_channel(self) -> None:

        """
        Delete all messages in Open Threads channel.
        """

        async for message in self.__channel_to_update.history(limit=None):
            await message.delete()
        return

    async def __update_channel(self) -> None:

        """
        Send messages to Open Threads channel
        """

        for message in self.__messages:
            await self.__channel_to_update.send(message)
        return


def setup(bot):
    bot.add_cog(ActiveThreads(bot))
