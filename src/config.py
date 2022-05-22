import os
from json import dump

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

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

# if no credential is found, search for it as enviromental variables
if not os.path.isfile("./credentials.json"):
    if os.path.isfile("./.env"):
        GOOGLE_CREDENTIALS_TYPE = os.getenv("GOOGLE_CREDENTIALS_TYPE")
        GOOGLE_CREDENTIALS_PROJECT_ID = os.getenv("GOOGLE_CREDENTIALS_PROJECT_ID")
        GOOGLE_CREDENTIALS_PRIVATE_KEY_ID = os.getenv(
            "GOOGLE_CREDENTIALS_PRIVATE_KEY_ID"
        )
        GOOGLE_CREDENTIALS_PRIVATE_KEY = os.getenv("GOOGLE_CREDENTIALS_PRIVATE_KEY")
        GOOGLE_CREDENTIALS_CLIENT_EMAIL = os.getenv("GOOGLE_CREDENTIALS_CLIENT_EMAIL")
        GOOGLE_CREDENTIALS_CLIENT_ID = os.getenv("GOOGLE_CREDENTIALS_CLIENT_ID")
        GOOGLE_CREDENTIALS_AUTH_URI = os.getenv("GOOGLE_CREDENTIALS_AUTH_URI")
        GOOGLE_CREDENTIALS_TOKEN_URI = os.getenv("GOOGLE_CREDENTIALS_TOKEN_URI")
        GOOGLE_CREDENTIALS_AUTH_PROVIDER = os.getenv("GOOGLE_CREDENTIALS_AUTH_PROVIDER")
        GOOGLE_CREDENTIALS_CLIENT = os.getenv("GOOGLE_CREDENTIALS_CLIENT")
    else:
        GOOGLE_CREDENTIALS_TYPE = os.environ["GOOGLE_CREDENTIALS_TYPE"]
        GOOGLE_CREDENTIALS_PROJECT_ID = os.environ["GOOGLE_CREDENTIALS_PROJECT_ID"]
        GOOGLE_CREDENTIALS_PRIVATE_KEY_ID = os.environ[
            "GOOGLE_CREDENTIALS_PRIVATE_KEY_ID"
        ]
        GOOGLE_CREDENTIALS_PRIVATE_KEY = os.environ["GOOGLE_CREDENTIALS_PRIVATE_KEY"]
        GOOGLE_CREDENTIALS_CLIENT_EMAIL = os.environ["GOOGLE_CREDENTIALS_CLIENT_EMAIL"]
        GOOGLE_CREDENTIALS_CLIENT_ID = os.environ["GOOGLE_CREDENTIALS_CLIENT_ID"]
        GOOGLE_CREDENTIALS_AUTH_URI = os.environ["GOOGLE_CREDENTIALS_AUTH_URI"]
        GOOGLE_CREDENTIALS_TOKEN_URI = os.environ["GOOGLE_CREDENTIALS_TOKEN_URI"]
        GOOGLE_CREDENTIALS_AUTH_PROVIDER = os.environ[
            "GOOGLE_CREDENTIALS_AUTH_PROVIDER"
        ]
        GOOGLE_CREDENTIALS_CLIENT = os.environ["GOOGLE_CREDENTIALS_CLIENT"]

    credentials = {
        "type": GOOGLE_CREDENTIALS_TYPE,
        "project_id": GOOGLE_CREDENTIALS_PROJECT_ID,
        "private_key_id": GOOGLE_CREDENTIALS_PRIVATE_KEY_ID,
        "private_key": GOOGLE_CREDENTIALS_PRIVATE_KEY,
        "client_email": GOOGLE_CREDENTIALS_CLIENT_EMAIL,
        "client_id": GOOGLE_CREDENTIALS_CLIENT_ID,
        "auth_uri": GOOGLE_CREDENTIALS_AUTH_URI,
        "token_uri": GOOGLE_CREDENTIALS_TOKEN_URI,
        "auth_provider_x509_cert_url": GOOGLE_CREDENTIALS_AUTH_PROVIDER,
        "client_x509_cert_url": GOOGLE_CREDENTIALS_CLIENT,
    }

    with open("./credentials.json", "w") as f:
        dump(credentials, f, indent=4)

# Use creds to create a client to interact with the Google Drive API
scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(credentials)

# Gets the spreadsheet's info (commands and triggers)
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
command_sheet = spreadsheet.worksheet("commands").get_all_records()
trigger_sheet = spreadsheet.worksheet("triggers").get_all_records()


def refresh_sheet():
    """
    Update the commands and triggers
    by getting the spreadsheet's info again
    """
    spreadsheet = client.open_by_key(SPREADSHEET_KEY)
    commandSheet = [
        record
        for record in spreadsheet.worksheet("commands").get_all_records()
        if record["COMMAND NAME"]
    ]
    triggerSheet = [
        record
        for record in spreadsheet.worksheet("triggers").get_all_records()
        if record["TRIGGER"]
    ]

    isEmpty = len(triggerSheet) == 0 and len(commandSheet) == 0

    return spreadsheet, commandSheet, triggerSheet, isEmpty
