from disnake import Embed
from disnake.ext import commands


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test_command(self, interaction):
        embed = Embed(
            title="Un titre pour mon embed",
            description="""
Le but est de trouver le jeu dont est tiré une image (complète ou partielle). Celui qui donne la bonne réponse devient le nouvau maître du jeu..
  
Le maître du jeu anime la partie avec des réactions sous les messages:
🔴 début du jeu, :orange_circle: indice supplémentaire, 🟢 bonne réponse
👎 :poucebasrouge: 💩 mauvaise réponse, 🤏 on s'approche (bonne série en général)
:correct: :correct_anim: :poucehautvert: oui (en réponse à une question), ❌ :Faux: :Faux_anim: non""",
            colour=0xF0C43F#,
            # timestamp=datetime.now(timezone.utc)
        )
        print(interaction.channel.id)
        await interaction.response.send_message('', embed=embed)


def setup(bot):
    bot.add_cog(TestClass(bot))
