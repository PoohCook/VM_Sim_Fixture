from typing import Callable, List
from .ht_frame import *
from .record import HtRecord
from functools import reduce
from operator import xor
import logging


VM_HT_CREDENTIALS_LENGTH = 20
VM_HT_KEY_MASK = [0x0d, 0x0b, 0x00, 0x06, 0x10]
VM_HT_KEY_CHECK = [0x0d, 0x0d, 0x00, 0x06, 0x10]


class HtRecordCodec():

    def set_htConfig(self, htConfig):
        if len(htConfig) != 50:
            raise ValueError("improper HT credentials")

        self.__htKeys = []
        for i in range(40, len(htConfig) - 1, 2):
            hexStr = htConfig[i:i + 2]
            self.__htKeys.append(int(hexStr, 16))

        sec_data = []
        for i in range(0, 39, 2):
            hexStr = htConfig[i:i + 2]
            sec_data.append(int(hexStr, 16))

        self.__htSecRecords = self.__parse_records(sec_data)
        self.__htCredentailsFrame = self.encodeRecords(self.__htSecRecords)[0]
        self.__current_htConfig = htConfig

    def update_htConfig(self, frame: HtDataFrame):
        frameData = frame.data[4:-2]
        if len(frameData) != VM_HT_CREDENTIALS_LENGTH:
            return None

        keys = []
        credentials = []
        keyLength = len(VM_HT_KEY_MASK)
        for i, data in enumerate(frameData):
            if i < keyLength:
                keys.append(data ^ VM_HT_KEY_MASK[i])
            credentials.append(data ^ keys[i % keyLength])

        if credentials[10: 15] == VM_HT_KEY_CHECK:
            update = "".join(["%02x" % c for c in credentials] + ["%02x" % k for k in keys])
            if update != self.__current_htConfig:
                self.set_htConfig(update)
                return update

    def getCredentialsFrame(self):
        return self.__htCredentailsFrame

    def decodeRecords(self, frames: List[HtDataFrame]) -> List[HtRecord]:
        frameData = []
        for i, frame in enumerate(frames):
            frameData.extend(frame.data)

        if len(frameData) < 4 or frameData[0] != 0xf2:
            raise ValueError("BAD record start:%s" % (frameData))

        # maybe someday we will care
        # record_length = int("%02x%02x" % (frameData[1], frameData[2]), 10)
        # record_index = frameData[3]

        check = reduce(xor, frameData[1:])
        check_data = frameData[-2:]
        if check_data[0] != 0xff or check != 0:
            raise ValueError("BAD record end frame or checksum:%s, %s, %s" % (frame, check, check_data[0]))

        recordData = self.__decode_data_frame(frameData[4:-2])
        return self.__parse_records(recordData)

    def encodeRecords(self, records: List[HtRecord]) -> List[HtDataFrame]:
        recordData = []
        for record in records:
            recordData.extend(record.render_data())

        return self.__render_frames(recordData)

    def __parse_records(self, recordData):
        records = []
        while recordData:
            record = HtRecord()
            recordData = record.parse_data(recordData)
            records.append(record)
        return records

    def __decode_data_frame(self, frameData):
        next_decode_index = 0
        unmaskedData = []
        key_span = len(self.__htKeys)
        for val in frameData:
            unmaskedData.append((val ^ self.__htKeys[next_decode_index % key_span]) & 0xff)
            next_decode_index += 1

        return unmaskedData

    def __encode_data_frame(self, data):
        next_decode_index = 0
        maskedData = []
        key_span = len(self.__htKeys)
        for val in data:
            maskedData.append((val ^ self.__htKeys[next_decode_index % key_span]) & 0xff)
            next_decode_index += 1

        return maskedData

    def __render_frames(self, data):
        length = len(data)
        index = 0
        len_str = "%0.4d" % (length + 2)
        frameData = [int(len_str[0:2], 16), int(len_str[2:4], 16), index]
        frameData.extend(self.__encode_data_frame(data))
        check = reduce(xor, frameData) ^ 0xff
        frameData = [0xf2, *frameData, 0xff, check]

        frame_size = 120
        frames = [HtDataFrame(data=frameData[i: i + frame_size]) for i in range(0, len(frameData), frame_size)]
        frames[-1].set_end()
        return frames
