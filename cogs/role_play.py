from disnake import AllowedMentions
from disnake.ext import commands
from random import randrange
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter


class RolePlay(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild = self.__bot.guilds[0]

    @commands.slash_command()
    async def dice(self, inter, lancers: int, faces: int):
        """
        Fait rouler Dédé.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} fait rouler Dédé sur {inter.channel.mention}.""",
            message_success=f"""Dédé a bien roulé.""",
            message_failure=f"""Dédé n'a pas pu rouler...""",
            task_info='command.role.dice',
            interaction=inter
        )
        await logger.log_start()

        if lancers < 1:
            await logger.log_message(f"""Le nombre de lancers ne peut pas être inférieur à 1.""")
            await logger.log_failure()
            return

        if faces < 1:
            await logger.log_message(f"""Le nombre de faces ne peut pas être inférieur à 1.""")
            await logger.log_failure()
            return

        text = f"{inter.author.mention} a lancé {lancers} dés à {faces} faces:"
        for i in range(lancers):
            text += f"\nLancer n°{i + 1} >> Résultat: **{randrange(1, faces + 1)}**"
        text_split: list[str] = MessageSplitter(text).get_message_split()
        for message in text_split:
            await inter.channel.send(message, suppress_embeds=True,
                                             allowed_mentions=AllowedMentions(users=False))

        await logger.log_success()
        return


def setup(bot):
    bot.add_cog(RolePlay(bot))
