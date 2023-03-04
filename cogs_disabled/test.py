from disnake import Embed, Permissions
from disnake.ext import commands


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test_embed(self, interaction):
        """
        Une description en docstring pour ma fonction.
        """

        embed = Embed(
            title="Un titre pour mon embed",
            description="Un body pour mon embed",
            colour=0xF0C43F
        )
        embed.set_author(name='sticky')
        # print(interaction.channel.id)
        await interaction.response.send_message('', embed=embed)

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def test_droits(self, inter):
        await inter.response.send_message('coucou')


def setup(bot):
    bot.add_cog(TestClass(bot))
