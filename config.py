import dotenv
import os

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not specified in .env")

HOME_GUILD_ID = os.getenv("HOME_GUILD_ID")
if not HOME_GUILD_ID:
    raise ValueError("HOME_GUILD_ID is not specified in .env")

MUSIC_CACHE_FOLDER = os.getenv("MUSIC_CACHE_FOLDER")
if not MUSIC_CACHE_FOLDER:
    raise ValueError("MUSIC_CACHE_FOLDER is not specified in .env")

MUSIC_CACHE_LIFETIME = os.getenv("MUSIC_CACHE_LIFETIME")
if not MUSIC_CACHE_LIFETIME:
    raise ValueError("MUSIC_CACHE_LIFETIME is not specified in .env")
else:
    MUSIC_CACHE_LIFETIME = int(MUSIC_CACHE_LIFETIME)

MUSIC_MAX_DOWNLOADERS = os.getenv("MUSIC_MAX_DOWNLOADERS")
if not MUSIC_MAX_DOWNLOADERS:
    raise ValueError("MUSIC_MAX_DOWNLOADERS is not specified in .env")
else:
    MUSIC_MAX_DOWNLOADERS = int(MUSIC_MAX_DOWNLOADERS)

FFMPEG = os.getenv("FFMPEG")
if not FFMPEG:
    raise ValueError("FFMPEG is not specified in .env")

FFPROBE = os.getenv("FFPROBE")
if not FFPROBE:
    raise ValueError("FFPROBE is not specified in .env")
