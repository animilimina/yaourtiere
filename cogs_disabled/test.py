from disnake.ext import commands
from config import config

class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test_command(self, interaction):
        print(interaction.channel.id)
        await interaction.response.send_message('réussi')


def setup(bot):
    bot.add_cog(TestClass(bot))
