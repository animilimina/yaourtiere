import disnake
from disnake.ext import commands
import json

@bot.event
async def on_thread_create(thread):
    # Load existing data from the file
    with open('threads.json', 'r') as file:
        thread_data = json.load(file)

    # Add a new object for the created thread
    thread_info = {
        'thread_name': thread.name,
        'thread_id': thread.id,
        'parent_channel_name': thread.parent.name if thread.parent else None,
        'parent_channel_id': thread.parent.id if thread.parent else None,
    }

    thread_data.append(thread_info)

    # Write the updated data back to the file
    with open('threads.json', 'w') as file:
        json.dump(thread_data, file, indent=4)

@bot.event
async def on_thread_delete(thread):
    # Load existing data from the file
    with open('threads.json', 'r') as file:
        thread_data = json.load(file)

    # Update the corresponding thread id with "Deleted"
    for thread_info in thread_data:
        if thread_info['thread_id'] == thread.id:
            thread_info['thread_id'] = 'Deleted'

    # Write the updated data back to the file
    with open('threads.json', 'w') as file:
        json.dump(thread_data, file, indent=4)

@bot.event
async def on_thread_update(before, after):
    # Load existing data from the file
    with open('threads.json', 'r') as file:
        thread_data = json.load(file)

    # Update the corresponding thread name and parent channel name
    for thread_info in thread_data:
        if thread_info['thread_id'] == before.id:
            thread_info['thread_name'] = after.name
            thread_info['parent_channel_name'] = after.parent.name if after.parent else None

    # Write the updated data back to the file
    with open('threads.json', 'w') as file:
        json.dump(thread_data, file, indent=4)

@bot.event
async def on_guild_channel_update(before, after):
    # Load existing data from the file
    with open('threads.json', 'r') as file:
        thread_data = json.load(file)

    # Update the corresponding channel name
    for thread_info in thread_data:
        if thread_info['parent_channel_id'] == before.id:
            thread_info['parent_channel_name'] = after.name

    # Write the updated data back to the file
    with open('threads.json', 'w') as file:
        json.dump(thread_data, file, indent=4)
