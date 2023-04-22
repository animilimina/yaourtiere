from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake.ext import commands


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def test(self, interaction):
        """
        Une description en docstring pour ma fonction.
        """
        message_start = await interaction.channel.fetch_message(1082701463115022377)
        async for message in interaction.channel.history(limit=10, after=message_start):
            text = "\n".join([attachment.url for attachment in message.attachments])
            print(text)
            if text:
                await interaction.channel.send(text)
        await interaction.response.send_message("success")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(reaction.emoji)

    @commands.message_command(name="Modérer")
    async def reverse(self, inter: ApplicationCommandInteraction, message: Message):
        # Reversing the message and sending it back.
        await inter.response.defer()
        # await message.clean_content
        # await message.channel.send
        await inter.edit_original_message(f"""
        **__MESSAGE MODÉRÉ__**\nAuteur: {message.author.mention}. Date: {message.created_at}\n||~~{message.content}~~||""")


def setup(bot):
    bot.add_cog(TestClass(bot))
