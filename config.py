import dotenv
import os

dotenv.load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN is not specified in .env')

HOME_GUILD_ID = os.getenv('HOME_GUILD_ID')
if not HOME_GUILD_ID:
    raise ValueError('HOME_GUILD_ID is not specified in .env')

FFMPEG = os.getenv('FFMPEG')
if not FFMPEG:
    raise ValueError('FFMPEG is not specified in .env')

FFPROBE = os.getenv('FFPROBE')
if not FFPROBE:
    raise ValueError('FFPROBE is not specified in .env')
