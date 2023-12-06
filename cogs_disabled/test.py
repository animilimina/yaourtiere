from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake import Guild, TextChannel
from disnake.ext import commands
from disnake.ui import Button, View
from tools.message_splitter import MessageSplitter


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]

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
    async def recherche(self, inter, mot: str):
        await inter.response.defer()
        channels = await self.__guild.fetch_channels()
        active_threads = await self.__guild.active_threads()
        full_list = []
        for channel in channels:
            full_list.extend([x for x in active_threads if x.parent == channel])
            if isinstance(channel, TextChannel):
                async for thread in channel.archived_threads(limit=None):
                    full_list.append(thread)

        filtered_list = [x for x in full_list if mot.lower() in x.name.lower()]

        if len(filtered_list) == 0:
            message = f"""{inter.author.mention} désolé, pas de résultat pour "**{mot}**". À vous de créer ce fil ;-)"""
            await inter.channel.send(message)
        else:
            message = f"""{inter.author.mention} vous trouverez "**{mot}**" dans :"""
            embed_text = '\n'.join([x.parent.name + ' > ' + x.jump_url for x in filtered_list])
            embed_text_splitter = MessageSplitter(embed_text)
            texts = embed_text_splitter.get_message_split()
            await inter.channel.send(message, embed=Embed(description=texts[0]))
            texts = texts[1:]
            while texts:
                await inter.channel.send(embed=Embed(description=texts[0]))
                texts = texts[1:]

        await inter.edit_original_message("done")
        await inter.delete_original_message(delay=2)


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
