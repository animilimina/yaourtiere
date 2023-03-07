from disnake import Embed, Permissions
from disnake.ext import commands


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test(self, interaction, something: str):
        """
        Une description en docstring pour ma fonction.
        """
        for item in something.split(' '):
            print(item)
        await interaction.response.send_message("bla")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(reaction.emoji)


def setup(bot):
    bot.add_cog(TestClass(bot))
