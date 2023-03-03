from tools.archivist.components.interactor import Interactor
from tools.archivist.components.reporter import Reporter
from tools.archivist.components.tracker import Tracker
from tools.message_splitter import MessageSplitter


class Logger:
    def __init__(self, bot, task_info: str, log_group: str = '', message_start: str = '', message_success: str = '',
                 message_failure: str = '', interaction=None):
        self.__logger = Reporter(bot)
        self.__interaction = interaction
        self.__interactor = Interactor(self.__interaction) if self.__interaction else None
        self.__tracker = Tracker(self.__interaction, task_info)
        self.__activity_was_tracked = False
        self.__user = interaction.user.mention if interaction else ''
        self.__variables = self.__build_variable_dictionary()
        self.__log_group = log_group
        self.__message_start = self.__replace_variables(message_start)
        self.__message_success = self.__replace_variables(message_success)
        self.__message_failure = self.__replace_variables(message_failure)

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
        self.__track_activity()
        if self.__interactor:
            await self.__interactor.defer()
        await self.__log(self.__message_start)

    async def __log(self, message):
        await self.__logger.log(f"{self.__log_group} : {message}" if self.__log_group else message)

    def __track_activity(self):
        if not self.__activity_was_tracked:
            self.__tracker.track_activity()
            self.__activity_was_tracked = True

    async def interaction_is_authorized(self, *groups: str) -> bool:
        if not self.__interactor.authorize(*groups):
            await self.__log_rejection()
            return False
        else:
            return True

    async def __log_rejection(self):
        await self.__interactor.reject()
        await self.__logger.reject(self.__user)

    async def log_message(self, message):
        message_split = MessageSplitter(message).get_message_split()
        for sub_message in message_split:
            await self.__logger.log(sub_message)

    async def log_success(self):
        self.__track_activity()
        if self.__interactor:
            await self.__interactor.success()
        await self.__log(self.__message_success)

    async def log_failure(self):
        self.__track_activity()
        if self.__interactor:
            await self.__interactor.failure()
        await self.__log(self.__message_failure)
