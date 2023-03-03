import disnake
from tools.archivist.logger import Logger
from tools.text_importers import read_yaml


class AuthorisationManager:
    def __init__(self, interaction):
        self.__interaction = interaction
        self.__bot = self.__interaction.bot
        self.__logger = Logger(self.__bot, interaction=interaction)

    def interaction_user_is_in_group(self, *groups: str) -> bool:
        user_groups = read_yaml('config/user_groups.yml')
        output = False
        for group in groups:
            output = True if self.__interaction.user.id in user_groups[group] else output
        return output

    async def reject_interaction(self):
        await self.__logger.log_rejection()
        await self.__interaction.response.send_message(
            self.__interaction.author.mention + ", tu n'es pas autorisé à passer cette commande",
            allowed_mentions=disnake.AllowedMentions(everyone=False, users=False),
            delete_after=2)
