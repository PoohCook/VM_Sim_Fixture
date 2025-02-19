#! /usr/bin/env python3
import re
from typing import List
from collections.abc import Iterable
from enum import Enum


class HexCodec():
    @staticmethod
    def encodeDataStr(data):
        if not isinstance(data, Iterable) or [c for c in data if not isinstance(c, int)]:
            raise ValueError(f"Invalid data list: {data}")

        return f"[{','.join([f'{c:02x}' for c in data])}]"

    @staticmethod
    def decodeDataStr(dataStr):
        if dataStr in [None, ""]:
            return []

        if not isinstance(dataStr, str) or re.search(r'[^\da-fA-F,\]\[ ]+', dataStr) is not None:
            raise ValueError(f"Invalid data string: {dataStr}")

        return [int(f"0x{v}", base=16) for v in dataStr.strip("[]").split(',') if v.strip(' ') != '']
