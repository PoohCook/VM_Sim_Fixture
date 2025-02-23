#! /usr/bin/env python3
import logging
from typing import Callable, List
from ..tenframe.ht import *
from .record import HtRecord
from .codec import HtRecordCodec
from ..tenio import TenIoListener, TenIoManager
from .ht_interface import *
from functools import reduce
from operator import xor
from enum import Enum
from .ht_base import *
from ..tenconfig import InventoryColumn
from .adaptor import TenHtAdaptor


class HtOpTypes(Enum):
    UNKNOWN = 0x00
    COLLECT_DATA = 0x01
    CLEAR_DATA = 0x02
    COLLECT_VM_SETTING_DATA = 0x03
    SET_VM_DATA_SETTING = 0x41
    ALL_CLEAR = 0x81
    CLEAR_CHECK = 0x87
    ALL_CLEAR_CHECK = 0x88
    COLLECT_ONLINE_DATA = 0x07
    SET_ONLINE_DATA = 0x46
    SET_WORK_DATA = 0x47
    ONLINE_DATA_ALL_CLEAR = 0x86
    ONLINE_DATA_ALL_CLEAR_CHECK = 0x89


class HtCounter():
    def __init__(self, code: int, item_length: int, items: List[Any] = None, length: int = None) -> None:
        self.code = code
        self.item_length = item_length
        self.items = items if items else []
        self.length = length if length else len(self.items)
        if len(self.items) != self.length:
            self.items = [0 for i in range(self.length)]

    def __encodeValue(self, value):
        if type(value) is int:
            return ("%%0%dd" % self.item_length) % value
        elif type(value) is str:
            return ("%%0%ds" % self.item_length) % value

    def update(self, items: List[Any]):
        for item in items:
            if len(item) != self.item_length:
                raise ValueError(f"All records to write must have length == {self.item_length}")

        self.items = items
        self.length = len(items)

    def encode(self):
        return HtRecord(ht_code=self.code,
                        item_length=self.item_length,
                        items=[self.__encodeValue(v) for v in self.items])


class TenSimulatedHtAdaptor(TenHtAdaptor):
    ORIGIN_IR = "IR"
    ORIGIN_MC = "MC"

    def __init__(self, extension: HtBase, monitorHandler: Callable[[str, List[HtRecord]], None] = None,
                 commandHandler: Callable[[List[HtRecord]], None] = None) -> None:
        super().__init__(extension, monitorHandler, commandHandler)
        self.data_cache = []

    def onConfigure(self, args):
        super().onConfigure(args)

    def onConfigUpdate(self, path, value):
        super().onConfigUpdate(path=path, value=value)

    def onStart(self):
        super().onStart()
        self.__initializeDataCache()

    def isSimulated(self):
        return self._config_args.get("simulatedVmMode")

    def __encodeTemperature(self, temp):
        if temp == InventoryColumn.TEMPERATURE_AMBIENT:
            return 0
        elif temp == InventoryColumn.TEMPERATURE_COLD:
            return 10
        elif temp == InventoryColumn.TEMPERATURE_HOT:
            return 20
        return 30

    def __initializeDataCache(self):
        columns = self._htExt.getInventoryColumns(column="all")
        column_count = len(columns)

        self.data_cache = [
            HtCounter(code=0x0bc0, item_length=14, items=[c.product_code for c in columns]),
            HtCounter(code=0x0bc3, item_length=4, items=[c.cash_price for c in columns]),
            HtCounter(code=0x0bc6, item_length=4, items=[c.card_price for c in columns]),
            HtCounter(code=0x0bc1, item_length=2, items=[self.__encodeTemperature(c.temperature) for c in columns]),
            HtCounter(code=0x0bc4, item_length=4, length=column_count),
            HtCounter(code=0x0c0b, item_length=6, length=column_count),
            HtCounter(code=0x0ba1, item_length=10, items=[0, 0]),
            HtCounter(code=0x0bb1, item_length=20, length=16),
            HtCounter(code=0x0bb2, item_length=20, length=16)
        ]

    def __getOperation(self, record: HtRecord):
        if record.ht_code != 0x0AA0:
            return HtOpTypes.UNKNOWN

        return HtOpTypes(int(f"0x{record.items[0]}", 16))

    def __getCounter(self, code, length_hint=None):
        for counter in self.data_cache:
            if counter.code == code:
                return counter

        if not length_hint:
            raise ValueError(f"Failed to find records for {code:04x}")

        counter = HtCounter(code=code, item_length=length_hint, length=1)
        self.data_cache.append(counter)
        return counter

    def __readRecords(self, codes: HtRecord):
        if codes.ht_code != 0x0A1A:
            raise ValueError(f"Unexpected HT code: {codes.ht_code}")

        response = []
        for code in codes.items:
            code = int(f"0x{code}", 16)

            counter = self.__getCounter(code)
            response.append(counter.encode())

        self._monitorHandler(origin="MC", records=response)

    def __updateRecord(self, codes: HtRecord):

        if len(codes.items) < 1:
            raise ValueError(f"Missing HT records to write")

        counter = self.__getCounter(codes.ht_code, length_hint=len(codes.items[0]))
        counter.update(codes.items)

    def sendRecords(self, records: List[HtRecord], response_handler: Callable[[List[int]], None] = None,
                          data_record: HtRecord = None):
        if not records:
            raise ValueError("records required to send")

        if not self.isSimulated():
            return super().sendRecords(records=records, response_handler=response_handler, data_record=data_record)

        operation = self.__getOperation(record=records[0])
        if operation in [HtOpTypes.COLLECT_DATA, HtOpTypes.COLLECT_ONLINE_DATA]:
            self.__readRecords(records[1])
        elif operation in [HtOpTypes.SET_VM_DATA_SETTING, HtOpTypes.SET_ONLINE_DATA]:
            self.__updateRecord(data_record)
