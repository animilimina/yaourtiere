from disnake import AllowedMentions
from tools.text_managers import read_yaml


class Interactor:
    """
    Slash command management
    """

    def __init__(self, interaction):
        self.__interaction = interaction
        self.__user = self.__interaction.user.mention
        self.__seconds_before_feedback_deletion = 2

    async def defer(self) -> None:
        """
        Send feedback to user while command is being processed
        """

        await self.__interaction.response.defer(with_message=True)

    def authorize(self, *groups: str) -> bool:
        user_groups = read_yaml('config/user_groups.yml')
        output = False
        for group in groups:
            output = True if self.__interaction.user.id in user_groups[group] else output
        return output

    async def reject(self) -> None:
        """
        Send rejection message to user
        """
        await self.__send_feedback(f"❌ {self.__user}, tu n'es pas autorisé à utiliser cette commande.")

    async def __send_feedback(self, message) -> None:
        """
        Send a message to the user, then delete it after a while.

        :param message: Message sent to the user
        """

        await self.__interaction.edit_original_message(message,
                                                       allowed_mentions=AllowedMentions(everyone=False, users=False))
        await self.__interaction.delete_original_message(delay=self.__seconds_before_feedback_deletion)

    async def success(self) -> None:
        """
        Send success message to the user
        """
        await self.__send_feedback(f"✅ {self.__user}, ta commande a réussi.")

