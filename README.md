# Discord Chat-Bot

Simple bot that'll reply to commands (prefix '>') and on_message() triggers specified in a Google Sheets.
The spreadsheet must have two worksheets named "triggers" and "commands", respectively.

## Commands' worksheet
It must have the following columns:
 - "COMMAND CATEGORY"
 - "COMMAND NAME"
 - "COMMAND ALIASES"
  - Multiple aliases should be separated by a linebreak;
  - Not necessary to include the command name.
 - "RESPONSE TEXT" - the reply's text content
 - "RESPONSE IMAGE" - public link to the reply's image content

## Triggers' worksheet
It must have the following columns:
 - "TRIGGER" - message content that'll trigger the reply below
  - Write it in lowercase - detection is not case-sensitive;
  - Multiple triggers should be separated by a linebreak.
 - "RESPONSE TEXT"
 - "RESPONSE IMAGE"
