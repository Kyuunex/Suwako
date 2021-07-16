from suwako.modules.storage_management import BOT_DATA_DIR
import os

if os.environ.get('SUWAKO_TOKEN'):
    bot_token = os.environ.get('SUWAKO_TOKEN')
else:
    try:
        with open(BOT_DATA_DIR + "/token.txt", "r+") as token_file:
            bot_token = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a bot token. either set SUWAKO_TOKEN environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit

if os.environ.get('SUWAKO_OSU_API_KEY'):
    osu_api_key = os.environ.get('SUWAKO_OSU_API_KEY')
else:
    try:
        with open(BOT_DATA_DIR + "/osu_api_key.txt", "r+") as token_file:
            osu_api_key = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a osu api key. either set SUWAKO_OSU_API_KEY environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit
