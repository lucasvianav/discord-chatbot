import os
from json import dump

import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Gets tokens and keys
if os.path.isfile('./.env'):
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    SPREADSHEET_KEY = os.getenv('SPREADSHEET_KEY')
    MONGODB_ATLAS_URI = os.getenv('MONGODB_ATLAS_URI')

else:
    DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
    SPREADSHEET_KEY = os.environ['SPREADSHEET_KEY']
    MONGODB_ATLAS_URI = os.environ['MONGODB_ATLAS_URI']

# if no credential is found, search for it as enviromental variables
if not os.path.isfile('./credentials.json'):
    if os.path.isfile('./.env'):
        TYPE = os.getenv("TYPE")
        PROJECT_ID = os.getenv("PROJECT_ID")
        PRIVATE_KEY_ID = os.getenv("PRIVATE_KEY_ID")
        PRIVATE_KEY = os.getenv("PRIVATE_KEY")
        CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
        CLIENT_ID = os.getenv("CLIENT_ID")
        AUTH_URI = os.getenv("AUTH_URI")
        TOKEN_URI = os.getenv("TOKEN_URI")
        AUTH_PROVIDER = os.getenv("AUTH_PROVIDER")
        CLIENT = os.getenv("CLIENT")

    else:
        TYPE = os.environ["TYPE"]
        PROJECT_ID = os.environ["PROJECT_ID"]
        PRIVATE_KEY_ID = os.environ["PRIVATE_KEY_ID"]
        PRIVATE_KEY = os.environ["PRIVATE_KEY"]
        CLIENT_EMAIL = os.environ["CLIENT_EMAIL"]
        CLIENT_ID = os.environ["CLIENT_ID"]
        AUTH_URI = os.environ["AUTH_URI"]
        TOKEN_URI = os.environ["TOKEN_URI"]
        AUTH_PROVIDER = os.environ["AUTH_PROVIDER"]
        CLIENT = os.environ["CLIENT"]

    credentials = {
        "type": TYPE,
        "project_id": PROJECT_ID,
        "private_key_id": PRIVATE_KEY_ID,
        "private_key": PRIVATE_KEY,
        "client_email": CLIENT_EMAIL,
        "client_id": CLIENT_ID,
        "auth_uri": AUTH_URI,
        "token_uri": TOKEN_URI,
        "auth_provider": AUTH_PROVIDER,
        "client": CLIENT
    }

    with open('./credentials.json', 'w') as f:
        dump(credentials, f, indent=4)

# Use creds to create a client to interact with the Google Drive API
scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)

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

