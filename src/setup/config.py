import os

import pymongo
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utilities.classes.spreadsheet import Spreadsheet

# Gets tokens and keys
if os.path.isfile("./.env"):
    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY")
    MONGODB_ATLAS_URI = os.getenv("MONGODB_ATLAS_URI")
else:
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
    SPREADSHEET_KEY = os.environ["SPREADSHEET_KEY"]
    MONGODB_ATLAS_URI = os.environ["MONGODB_ATLAS_URI"]

sheet = Spreadsheet(SPREADSHEET_KEY)

__intents = discord.Intents.default()
__intents.members = True
bot = commands.Bot(command_prefix=">", intents=__intents)

__client = pymongo.MongoClient(MONGODB_ATLAS_URI)
db = __client["discord-bot"]["discord-bot"]
