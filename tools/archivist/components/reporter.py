from config import config
from disnake import AllowedMentions


class Reporter:
    """
    Reports activity in the bot log thread
    """
    def __init__(self, bot):
        self.__channel = bot.get_channel(config.log_thread)

    async def log(self, message) -> None:
        """
        Forwards a message to the __post method (that will send it to the log thread)

        :param message: Message to be sent to the log thread
        """
        await self.__post(message)

    async def __post(self, message):
        """
        Sends a message to the log thread.

        :param message: Message to be posted.
        """

        await self.__channel.send(content=message, allowed_mentions=AllowedMentions(everyone=False, users=False))

    async def reject(self, user):
        """
        Forwards a rejection message to the __post method (that will send it to the log thread)

        :param user: ID that run the command
        """

        await self.__post(f"La demande de {user} a été rejetée.")
