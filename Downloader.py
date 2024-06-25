import asyncio
import logging
import typing


# класс загрузчика файлов
class Downloader:
    # логгер
    logger = logging.getLogger("downloader")

    def __init__(self, max_downloader_threads: int):
        # семафор на одновременное скачивание файлов
        self.downloaderSemaphore: asyncio.Semaphore = asyncio.Semaphore(max_downloader_threads)

    # корутина загрузки файла, принимающая синхронную функцию и имя целевого файла
    async def downloadFile(self, filename: str, download_function: typing.Callable) -> None:
        self.logger.info(f'Downloading of "{filename}" is queued.')
        await self.downloaderSemaphore.acquire()

        try:
            self.logger.info(f'Downloading of "{filename}" started.')
            await asyncio.to_thread(download_function)
        finally:
            self.logger.info(f'Downloading of "{filename}" finished.')
            self.downloaderSemaphore.release()
