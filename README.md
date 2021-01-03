# Discord Chat-Bot

Simple bot that'll reply to commands (prefix '>') and on_message() triggers specified in a Google Sheets.
The spreadsheet must have two worksheets named "triggers" and "commands", respectively.

In order to run, you must provide your own Google Sheets API's credentials.json and .env.
The .env file consists in a DISCORD_TOKEN and a SPREADSHEET_KEY, as can be seen in the .env.example file.

## DISCORD_TOKEN
You must create a discord application in https://discord.com/developers/applications/ and a bot inside it. The token needed is the bot's one, that can be found in https://discord.com/developers/applications/<APPLICATION ID\>/bot - as can be seen in the image below.

![](discord-token-example.png "Where to get the DISCORD_TOKEN")

## SPREADSHEET_KEY
Get it from the spreadsheet's link: https://docs.google.com/spreadsheets/d/<SPREADSHEET_KEY>.
Also, you must share the spreadsheet with your bot's email (from the Google Sheets API).

## Commands' worksheet
It must have the following columns:
 - "COMMAND CATEGORY"
 - "COMMAND NAME"
 - "COMMAND ALIASES"
 - - Multiple aliases should be separated by a linebreak;
 - - Not necessary to include the command name.
 - "RESPONSE TEXT" - the reply's text content
 - "RESPONSE IMAGE" - public link to the reply's image content

## Triggers' worksheet
It must have the following columns:
 - "TRIGGER" - message content that'll trigger the reply below
 - - Write it in lowercase - detection is not case-sensitive;
 - - Multiple triggers should be separated by a linebreak.
 - "RESPONSE TEXT"
 - "RESPONSE IMAGE"
