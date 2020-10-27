import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Gets tokens and keys
with open(".secrets.json", "r") as f: data = json.load(f)
DISCORD_TOKEN = data["discord-token"]
SPREADSHEET_KEY = data["spreadsheet-key"]

# Use creds to create a client to interact with the Google Drive API
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
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
    commandSheet = spreadsheet.worksheet("commands").get_all_records()
    triggerSheet = spreadsheet.worksheet("triggers").get_all_records()

    isEmpty = True if len(triggerSheet) == 0 and len(commandSheet) == 0 else False

    return spreadsheet, commandSheet, triggerSheet, isEmpty
