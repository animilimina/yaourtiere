from disnake import Member
from disnake.ext.commands import Cog, InteractionBot, slash_command
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_text


class WelcomeMessage(Cog):
    def __init__(self, bot: InteractionBot):
        self.__bot: InteractionBot = bot

    # @commands.Cog.listener()
    # async def on_member_join(self, member: Member):
    @slash_command()
    async def welcome(self, interaction):
        """
        Envoie un message de bienvenue aux nouveaux membres rejoignant le serveur.
        """

        member: Member = interaction.author
        logger: Logger = Logger(
            self.__bot,
            log_group='Tâche',
            message_start=f"""{member.mention} a rejoint le serveur.""",
            message_success=f"""Un message de bienvenue a été envoyé à {member.mention}.""",
            message_failure=f"""Echec de l'envoi du message de bienvenue à {member.mention}.""",
            task_info='task.private.welcome',
            interaction=interaction
        )
        await logger.log_start()
        text: str = read_text("config/welcome_message.txt")
        text_split: list[str] = MessageSplitter(text).get_message_split()

        for message in text_split:
            await member.send(message)

        await logger.log_success()
        return


def setup(bot):
    bot.add_cog(WelcomeMessage(bot))
