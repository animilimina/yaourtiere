import disnake
from disnake.ext import commands
from services.dynamodb import DynamodbItem


class ChannelItem(DynamodbItem):
    def __init__(self, channel_id: int):
        super().__init__('channel', channel_id)

    def is_test(self) -> bool:
        if "is_test" not in self._item.keys():
            self._item["is_test"] = False
            self._update_item()
        return self._item["is_test"]

    def make_test_start(self) -> None:
        if not self.is_test():
            self._item["is_test"] = False
            self._item["test_id"] = 0
            self._update_item()
        return

    def make_test_end(self) -> None:
        self._item["is_test"] = True
        self._update_item()

    def new_test(self) -> int:
        self._item["test_id"] += 1
        self._update_item()
        return self._item["test_id"]

    def get_test(self) -> int:
        return self._item["test_id"]


class TestItem(DynamodbItem):
    def __init__(self, channel_id: int, test_id: int):
        super().__init__(f'test_{str(channel_id)}', test_id)

    def set_enigma(self, message):
        self._item["channel_id"] = message.channel.id
        self._item["author"] = message.author.id
        self._item["enigma"] = {
            "message_id": message.id,
            "body": message.content,
            "attachments": [attachment.url for attachment in message.attachments]
        }
        self._update_item()

    def add_clue(self, message):
        self._item["clues"] = [] if "clues" not in self._item.keys() else self._item["clues"]
        self._item["clues"].append({
            "message_id": message.id,
            "body": message.content,
            "attachments": [attachment.url for attachment in message.attachments]
        })
        self._update_item()

    def set_answer(self, message):
        self._item["answer"] = {
            "message_id": message.id,
            "body": message.content,
            "attachments": [attachment.url for attachment in message.attachments]
        }
        self._update_item()

    def add_wrong_answer(self, message, reaction):
        self._item["wrong"] = [] if "wrong" not in self._item.keys() else self._item["wrong"]
        self._item["wrong"].append({
            "message_id": message.id,
            "body": message.content,
            "attachments": [attachment.url for attachment in message.attachments],
            "reaction": reaction
        })
        self._update_item()

    def add_question(self, message, reaction):
        self._item["question"] = [] if "question" not in self._item.keys() else self._item["question"]
        self._item["question"].append({
            "message_id": message.id,
            "body": message.content,
            "attachments": [attachment.url for attachment in message.attachments],
            "reaction": reaction
        })
        self._update_item()


class TestManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user = self.bot.user

    @commands.slash_command()
    async def make_test(self, inter):
        await inter.response.send_message(f"Nous transformons ce fil en test, cela peut prendre plusieurs heures, vous pouvez continuer à jouer en attendant.")
        channel_id = inter.channel.id
        channel_item = ChannelItem(channel_id)
        channel_item.make_test_start()
        async for message in inter.channel.history(limit=None, oldest_first=True):
            reactions = []
            for emoji in [reaction.emoji for reaction in message.reactions]:
                if type(emoji) == str:
                    reactions.append(emoji)
                else:
                    reactions.append(emoji.name)

            if not reactions:
                pass
            elif '🔴' in reactions:
                test_item = TestItem(channel_id, channel_item.new_test())
            else:
                test_item = TestItem(channel_id, channel_item.get_test())

            if not reactions:
                pass
            elif '🔴' in reactions:
                test_item.set_enigma(message)
            elif '🟠' in reactions:
                test_item.add_clue(message)
            elif '🟢' in reactions or 'poucehautvert' in reactions:
                test_item.set_answer(message)
            elif '🤏' in reactions:
                test_item.add_wrong_answer(message, '🤏')
            elif 'poucebasrouge' in reactions:
                test_item.add_wrong_answer(message, 'poucebasrouge')
            elif 'correct_anim' in reactions or 'correct' in reactions:
                test_item.add_question(message, 'correct')
            elif 'Faux_anim' in reactions or 'Faux' in reactions:
                test_item.add_question(message, 'Faux')

        channel_item.make_test_end()
        await inter.channel.send(f"Nous avons remonté la totalité de l'historique. La collecte se fera en temps réel à partir de maintenant.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return

        channel_id = reaction.message.channel.id
        channel_item = ChannelItem(channel_id)
        if not channel_item.is_test():
            return

        if type(reaction.emoji) == str:
            emoji = reaction.emoji
        else:
            emoji = reaction.emoji.name

        if emoji == '🔴':
            test_id = channel_item.new_test()
        else:
            test_id = channel_item.get_test()

        test_item = TestItem(channel_id, test_id)
        message = await reaction.message.channel.fetch_message(reaction.message.id)

        if emoji == '🔴':
            test_item.set_enigma(message)
        elif emoji == '🟠':
            test_item.add_clue(message)
        elif emoji in ['🟢', 'poucehautvert']:
            test_item.set_answer(message)
        elif emoji == '🤏':
            test_item.add_wrong_answer(message, '🤏')
        elif emoji == 'poucebasrouge':
            test_item.add_wrong_answer(message, 'poucebasrouge')
        elif emoji in ['correct_anim', 'correct']:
            test_item.add_question(message, 'correct')
        elif emoji in ['Faux_anim', 'Faux']:
            test_item.add_question(message, 'Faux')




def setup(bot):
    bot.add_cog(TestManager(bot))