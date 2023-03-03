from dotenv import load_dotenv
import os

load_dotenv()

working_environment = os.environ['working_environment']

discord_bot_token = os.environ['discord_bot_token']
discord_guild = int(os.environ['discord_guild'])
log_thread = int(os.environ['log_thread'])
reporting_thread = int(os.environ['reporting_thread'])

aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']
aws_region_name = os.environ['aws_region_name']

dynamodb_table = os.environ['dynamodb_table']