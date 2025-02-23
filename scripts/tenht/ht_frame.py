from typing import Callable, List


class HtDataFrame():
    def __init__(self, data: List[int], is_end=False) -> None:
        self.data = data
        self.is_end = is_end

    def set_end(self, value=True):
        self.is_end = value
