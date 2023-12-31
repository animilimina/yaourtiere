from disnake import Guild, Message
from disnake.ext import commands
import math
from services.Amplitude import core as amplitude


class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if self.__there_is_nothing_to_do(message):
            return
        event = {

            "user_id": str(message.author.id),
            "device_id": str(message.author.id),
            "time": math.floor(message.created_at.timestamp() * 1000),
            "event_type": "Message",
            "user_properties": {
                "username": message.author.display_name,
                "role": [x.name for x in message.author.roles],
                "top_role": message.author.top_role.name,
                "is_bot": message.author.bot
            },
            "event_properties": {
                "channel_id": message.channel.id,
                "channel_name": message.channel.name,
                "parent_id": message.channel.parent.id if hasattr(message.channel, 'parent') else message.channel.id,
                "parent_name": message.channel.parent.name if hasattr(message.channel, 'parent') else message.channel.name,
                "characters": len(message.content),
                "attachments": len(message.attachments)
            }
        }

        tracker = amplitude.AmplitudeManager()
        tracker.track(event)
        return

    def __there_is_nothing_to_do(self, message: Message) -> bool:
        if message.author == self.__bot.user:
            return True
        return False


def setup(bot):
    bot.add_cog(ActivityTracker(bot))
