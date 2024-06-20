import enum


class LoopType(enum.Enum):
    Off = 0
    Single = 1
    All = 2


class LoopedQueue[T]:
    def __init__(self, source: list[T] = None, loop: LoopType = LoopType.Off) -> None:
        self.queue: list[T] = source or []
        self._loop: LoopType = loop
        self._index: int = 0

    @property
    def loop(self) -> LoopType:
        return self._loop

    @loop.setter
    def loop(self, value: LoopType) -> None:
        if value == self._loop:
            return

        del self.queue[: self._index]
        self._index = 0
        self._loop = value

    @property
    def index(self) -> int:
        return self._index

    @property
    def empty(self) -> bool:
        return len(self.queue) == 0

    def get(self) -> T:
        if self.empty:
            return

        if self.loop in [LoopType.Off, LoopType.Single]:
            return self.queue[0]
        elif self.loop == LoopType.All:
            return self.queue[self._index]

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

    def add(self, item: list[T]) -> None:
        self.queue.extend(item)

    def clear(self) -> T:
        current = self.get()

        self.queue.clear()
        self._index = 0

        return current
