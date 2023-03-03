from disnake.ext import commands, tasks


class TestCollector:
    def __init__(self):
        pass

    @commands.slash_command()
    async def test_collector_initialise(self):
        # If db item exists -> pass
        # Create db thread item
        # Collect test history
        # Set db thread item to active
        pass

    @commands.slash_command()
    async def test_collector_pause(self):
        # If db item does not exist -> pass
        # If already paused -> pass
        # Set deb thread item to inactive
        pass

    @commands.slash_command()
    async def test_collector_resume(self):
        # If db item does not exist -> pass
        # If not paused -> pass
        # Collect test history
        # Set db thread item to active
        pass

    @tasks.loop(hours=3)
    async def collect_recent_tests(self):
        # Collect test history
        pass

    # History collector
        # Get last message collected -> thread item
        # Loop through messages since then
        # Only store full tests? -> No we can use a current test item
        # For each test, increase counter for game master and winner

# Tester si on peut ajouter plusieurs cogs à la fois dans la fonction