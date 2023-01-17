from config import config
from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake.ext import commands, tasks
from tools.archivist.logger import Logger
from tools.text_importers import read_yaml


class ActiveThreads(commands.Cog):

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
        self.__date = datetime.now(tz=timezone.utc)
        self.__settings = self.__read_settings()

    @tasks.loop(hours=1)
    async def refresh_open_threads_list(self) -> None:
        logger = Logger(
            self.__bot,
            log_group='Tâche automatisée ',
            message_start=f'Mise à jour du salon {self.__channel_to_update.mention}.',
            message_success=f'Mise à jour du salon {self.__channel_to_update.mention} terminée.',
            task_info='task.update.active threads'
        )

        await logger.log_start()

        self.__initialize_run()
        await self.__build_channel_thread_list()
        await self.__build_message_list()
        await self.__update_active_threads_channel()

        await logger.log_success()
        return

    async def __build_channel_thread_list(self) -> None:
        self.__channel_threads = []
        threads = await self.__guild.active_threads()

        while threads:
            channel = threads[0].parent
            threads_channel = [thread for thread in threads if thread.parent == channel]

            channel_dictionary = {
                "channel": channel,
                "threads": [thread for thread in threads_channel if not await self.__thread_is_dead(thread)]
            }

            if len(channel_dictionary["threads"]) > 0:
                self.__channel_threads.append(channel_dictionary)

            for thread in threads_channel:
                threads.remove(thread)

    async def __thread_is_dead(self, thread) -> bool:
        archive_date = await self.__get_thread_archive_date(thread)
        return archive_date < datetime.now(tz=timezone.utc)

    async def __get_thread_archive_date(self, thread) -> datetime:
        up_timestamp = thread.archive_timestamp
        try:
            last_message = await self.__get_thread_last_message_date(thread)
        except:
            last_message = up_timestamp
        last_activity = last_message if last_message > up_timestamp else up_timestamp
        return last_activity + timedelta(minutes=thread.auto_archive_duration)

    @staticmethod
    async def __get_thread_last_message_date(thread) -> datetime:
        message_list = []
        async for item in thread.history(limit=1):
            message_list.append(item)
        last_message = message_list[0]
        return last_message.created_at

    async def __build_message_list(self) -> None:
        instructions = f"""
Au {self.__date.astimezone(tz=tz.gettz('Europe/Paris')).strftime("%d/%m/%Y, %H:%M:%S")} (heure de Paris), voici la liste des fils actifs sur ce serveur Discord.

**__Légende :__**
> :{self.__settings["new"]["emoji"]}: = {self.__settings["new"]["description"]}
> :{self.__settings["up"]["emoji"]}: = {self.__settings["up"]["description"]}
> :{self.__settings["dying"]["emoji"]}: = {self.__settings["dying"]["description"]}
        """

        self.__messages = [instructions]
        for channel in self.__channel_threads:
            self.__complete_last_message('\n\n\n')
            self.__complete_last_message(channel["channel"].mention)

            for thread in channel["threads"]:
                thread_string = f"\n> {thread.mention}"
                thread_string += self.__add_new_emoji_if_required(thread)
                thread_string += self.__add_up_emoji_if_required(thread)
                thread_string += await self.__add_dying_emoji_if_required(thread)
                self.__complete_last_message(thread_string)

        return

    def __complete_last_message(self, string_to_add) -> None:
        last_message_length = len(self.__messages[-1])
        string_to_add_length = len(string_to_add)

        if last_message_length + string_to_add_length <= self.__settings["max_message_length"]:
            self.__messages[-1] += string_to_add
        else:
            self.__messages.append(string_to_add)

    def __add_new_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["new"]
        hours_since_creation = (self.__date - thread.created_at).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_since_creation < hours_for_emoji else ""
        return output

    def __add_up_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["up"]
        thread_is_new = thread.archive_timestamp + timedelta(minutes=-5) < thread.created_at
        hours_since_up = (self.__date - thread.archive_timestamp).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_since_up < hours_for_emoji and not thread_is_new else ""
        return output

    async def __add_dying_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["dying"]
        archive_date = await self.__get_thread_archive_date(thread)
        hours_until_archive = (archive_date - self.__date).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        output = f" :{parameters['emoji']}:" if hours_until_archive < hours_for_emoji else ""
        return output

    async def __update_active_threads_channel(self) -> None:
        await self.__delete_old_messages()
        await self.__send_new_messages()

    async def __delete_old_messages(self) -> None:
        async for message in self.__channel_to_update.history(limit=None):
            await message.delete()

    async def __send_new_messages(self) -> None:
        for message in self.__messages:
            await self.__channel_to_update.send(message)

def setup(bot):
    bot.add_cog(ActiveThreads(bot))
