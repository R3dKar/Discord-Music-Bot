from MusicBot import MusicBot
import logging
import logging.handlers
import datetime
import os

from config import BOT_TOKEN, LOG_FOLDER

# точка входа
if __name__ == "__main__":
    # дополнительное логирование в файл
    if LOG_FOLDER:
        logFilename = os.path.join(LOG_FOLDER, f"{datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S")}.log")
        fileHandler = logging.handlers.RotatingFileHandler(logFilename, maxBytes=10*2**20, backupCount=5)
        
        fileFormatter = logging.Formatter('[{asctime}.{msecs:03.0f}] [{levelname:<8}] {name}: {message}', "%Y.%m.%d %H:%M:%S", style='{')
        fileHandler.setFormatter(fileFormatter)
        
        rootLogger = logging.getLogger()
        rootLogger.addHandler(fileHandler)

    # запуск бота
    bot = MusicBot()
    bot.run(BOT_TOKEN, root_logger=True)
