from typing import List


class HtCounter():
    def __init__(self, cfg: dict) -> None:
        self.name = cfg["name"]
        self.ht_code = int(cfg["ht_code"], 16)
        self.size = cfg["size"]
        self.values = [int(c, 10) for c in cfg["values"]]

    def encode_values(self):
        return [f"{c:0{self.size}d}" for c in self.values]

    def render(self):
        return {
            "name": self.name,
            "ht_code": f"{self.ht_code:04X}",
            "size": self.size,
            "values": self.encode_values()
        }
