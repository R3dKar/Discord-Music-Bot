from MusicBot import MusicBot

from config import BOT_TOKEN

# точка входа
if __name__ == "__main__":
    bot = MusicBot()
    bot.run(BOT_TOKEN, root_logger=True)
