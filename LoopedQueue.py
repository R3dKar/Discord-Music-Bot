import enum


# перечисление типа зацикливания
class LoopType(enum.Enum):
    Off = 0  # отключено
    Single = 1  # один трек
    All = 2  # вся очередь


# класс очереди с поддержкой зацикливания
class LoopedQueue[T]:
    def __init__(self, source: list[T] = None, loop: LoopType = LoopType.Off) -> None:
        # очередь
        self.queue: list[T] = source or []
        # тип зацикливания
        self._loop: LoopType = loop
        # индекс в очереди
        self._index: int = 0

    # геттер типа зацикливания
    @property
    def loop(self) -> LoopType:
        return self._loop

    # сеттер типа зацикливания
    @loop.setter
    def loop(self, value: LoopType) -> None:
        # если такой же тип зацикливания, то скипнуть
        if value == self._loop:
            return

        # удалить треки, которые уже были в очереди ранее
        del self.queue[: self._index]
        self._index = 0
        self._loop = value

    # геттер индекса
    @property
    def index(self) -> int:
        return self._index

    # геттер значения, пустая ли очередь или нет
    @property
    def empty(self) -> bool:
        return len(self.queue) == 0

    # возвращает текущий элемент в очереди
    def get(self) -> T:
        if self.empty:
            return

        if self.loop in [LoopType.Off, LoopType.Single]:
            return self.queue[0]
        elif self.loop == LoopType.All:
            return self.queue[self._index]

    # сдвигает позицию в очереди на следующий элемент
    def next(self) -> None:
        if self.empty:
            return

        if self.loop == LoopType.Off:
            self.queue.pop(0)
        elif self.loop == LoopType.Single:
            pass
        elif self.loop == LoopType.All:
            self._index += 1
            if self._index >= len(self.queue):
                self._index = 0

    # добавить в очередь элементы
    def add(self, item: list[T]) -> None:
        self.queue.extend(item)

    # очистить очередь
    def clear(self) -> None:
        self.queue.clear()
        self._index = 0
