from tools.archivist.components.interactor import Interactor
from tools.archivist.components.reporter import Reporter
from tools.archivist.components.tracker import Tracker
from tools.message_splitter import MessageSplitter


class Logger:
    def __init__(self, bot, log_group: str = '', message_start: str = '', message_success: str = '',
                 interaction=None, task_info: str = ''):
        self.__logger = Reporter(bot)
        self.__interaction = interaction
        self.__interactor = Interactor(self.__interaction) if self.__interaction else None
        self.__tracker = Tracker(self.__interaction, task_info)
        self.__user = interaction.user.mention if interaction else ''
        self.__variables = self.__build_variable_dictionary()
        self.__log_group = log_group
        self.__message_start = self.__replace_variables(message_start)
        self.__message_success = self.__replace_variables(message_success)

    def __build_variable_dictionary(self):
        output = {
            'user': self.__user if self.__user else ''
        }
        return output

    def __replace_variables(self, text):
        for variable in self.__variables:
            text = text.replace(f"${{{variable}}}", self.__variables[variable])
        return text

    async def log_start(self):
        await self.__tracker.track_activity()
        if self.__interactor:
            await self.__interactor.defer()
        await self.__logger.log(f"{self.__log_group}: {self.__message_start}")

    async def log_rejection(self):
        await self.__interactor.reject()
        await self.__logger.reject(self.__user)

    async def log_message(self, message):
        message_split = MessageSplitter(message).get_message_split()
        for sub_message in message_split:
            await self.__logger.log(sub_message)

    async def log_success(self):
        if self.__interactor:
            await self.__interactor.success()
        await self.__logger.log(f"{self.__log_group}: {self.__message_success}")
