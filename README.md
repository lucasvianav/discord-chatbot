# Discord Chat-Bot

Simple bot that'll reply to commands (prefix '>') and on_message() triggers specified in a Google Sheets.
The spreadsheet must have two worksheets named "triggers" and "commands", respectively.

## Commands' worksheet
It must have the following columns:
 - "COMMAND CATEGORY"
 - "COMMAND NAME"
 - "COMMAND ALIASES"
 - "RESPONSE TEXT" - the reply's text content
 - "RESPONSE IMAGE" - public link to the reply's image content

## Triggers' worksheet
It must have the following columns:
 - "TRIGGER" - message content that'll trigger the reply below
 - "RESPONSE TEXT"
 - "RESPONSE IMAGE"
