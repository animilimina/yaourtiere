from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake.ext import commands
from disnake.ui import Button, View


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.slash_command()
    async def show(self, inter):
        await inter.channel.send('bla')
        return

    @show.sub_command()
    async def text(self, inter, input: str):
        await inter.response.send_message(input)
        return

    @show.sub_command()
    async def number(self, inter, input: str):
        await inter.channel.send(input)
        await inter.response.send_message('done')
        return

    @commands.slash_command()
    async def bouton(self, inter, input: str):
        await inter.response.defer()
        view = View()
        button = Button(label=input, url=inter.channel.jump_url)
        view.add_item(button)
        await inter.channel.send("voici le bouton", view=view)
        await inter.response.send_message("done")


def setup(bot):
    bot.add_cog(TestClass(bot))
