from os import getenv

import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

# Gets tokens and keys
DISCORD_TOKEN = getenv('DISCORD_TOKEN')
SPREADSHEET_KEY = getenv('SPREADSHEET_KEY')
MONGODB_ATLAS_URI = getenv('MONGODB_ATLAS_URI')

# Use creds to create a client to interact with the Google Drive API
scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Gets the spreadsheet's info (commands and triggers)
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
commandSheet = spreadsheet.worksheet("commands").get_all_records()
triggerSheet = spreadsheet.worksheet("triggers").get_all_records()

# Function to update the commands and triggers
# by getting the spreadsheet's info again
def refreshSheet():
    # Refreshes the sheet's data
    spreadsheet = client.open_by_key(SPREADSHEET_KEY)
    commandSheet = [ record for record in spreadsheet.worksheet("commands").get_all_records() if record["COMMAND"] ]
    triggerSheet = [ record for record in spreadsheet.worksheet("triggers").get_all_records() if record["TRIGGER"] ]

    isEmpty = len(triggerSheet) == 0 and len(commandSheet) == 0

    return spreadsheet, commandSheet, triggerSheet, isEmpty

