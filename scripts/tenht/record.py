from typing import Callable, List
import logging


def splice_bcd(data):
    return "".join(["%0.2x" % v for v in data])


def render_data_bytes(hex_str):
    return [int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)]


class HtRecord():
    def __init__(self, ht_code=None, item_length=None, items=None) -> None:
        self.ht_code = ht_code
        self.item_length = item_length
        self.items = items

    def _description(self):
        return "%s(code:%0.4x data:%s)" % (self.__class__.__name__, self.ht_code, self.items)

    def __str__(self):
        return self._description()

    def __repr__(self):
        return self._description()

    def __eq__(self, other):
        if not isinstance(other, HtRecord):
            return NotImplemented

        return self.ht_code == other.ht_code and self.item_length == other.item_length and self.items == other.items

    def parse_data(self, data: List[int]) -> int:
        try:
            self.ht_code = (data[0] << 8) + data [1]
            length = int(splice_bcd(data[2:4]))
            self.item_length = int(splice_bcd(data[4:5]))
            item_bytes = int(self.item_length / 2)
            item_count = int((length - 1) / item_bytes)
            data = data[5:]
            self.items = [splice_bcd(data[i * item_bytes: (i + 1) * item_bytes]) for i in range(item_count)]

            if len(data) > length - 1:
                return data[length - 1:]
        except Exception as e:
            logging.error(f"Error parsing data: {e}")

        return []

    def render_data(self):
        data = []
        data.extend(render_data_bytes("%0.4x" % (self.ht_code & 0xffff)))
        length = (len(self.items) * (self.item_length / 2)) + 1
        if length > 1024:
            length = 1024
        data.extend(render_data_bytes("%0.4d" % (length)))
        data.extend(render_data_bytes("%0.2d" % (self.item_length)))
        render_str = "%%0.%ds" % self.item_length
        for item in self.items:
            data.extend(render_data_bytes(render_str % (item)))

        return data
