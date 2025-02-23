from typing import List
from .adaptor import TenHtAdaptor
from .record import HtRecord
from .ht_interface import *
from .ht_base import HtBase
from .simulated_adaptor import TenSimulatedHtAdaptor
from ..tenextension import BeaconLogging
from modules.tenconfig import *
import logging


HT_CONFIG = "htConfig"


class HtExtension(HtBase):
    @classmethod
    def configValidators(cls):
        return {
            "Beacon": {
                "htConfig": ValidateHexStr(50, 50),
                "extensions": {
                    "HtExtension": {
                        "share": [
                            "htConfig",
                            "simulatedVmMode"
                        ]
                    }
                }
            }
        }

    def initialize(self):
        self.__htAdaptor = TenSimulatedHtAdaptor(extension=self,
                                                 monitorHandler=self.__onRecordReceived,
                                                 commandHandler=self.__onCommandReceived)
        self.__config_args = {}

    def onConfigure(self, args):
        self.__config_args = args
        self.__htAdaptor.onConfigure(self.__config_args)
        self.addConfigUpdates("Beacon.htConfig")
        return True

    def onConfigUpdate(self, path, value):
        logging.info("HtConfig updated to: %s", value)
        self.__htAdaptor.onConfigUpdate(path=path, value=value)

    def onStart(self):
        self.__htAdaptor.onStart()

    def onShutdown(self):
        pass

    def __onRecordReceived(self, origin: str, records: List[HtRecord]):
        for record in records:
            logging.info(f"HT Record: {record}")
        self.onHTRecordsUpdate(origin=origin, records=records)
        for i, record in enumerate(records):
            self.onHTResponseUpdate(
                frame=i,
                last=(i == (len(records) - 1)),
                response="%0.4X" % record.ht_code,
                data=record.items,
                datalength=len(record.items),
                itemlength=record.item_length,
                recipient=origin
            )

    def __onCommandReceived(self, records: List[HtRecord]):
        for record in records:
            logging.info(f"HT Command: {record}")
        for i, record in enumerate(records):
            self.onHTCommandUpdate(
                frame=i,
                last=(i == (len(records) - 1)),
                command="%0.4X" % record.ht_code,
                data=record.items,
                datalength=len(record.items),
                itemlength=record.item_length
            )

    def __compose_command(self, commandType):
        if commandType == SEND_COMMAND_TYPE_OFFLINE_GET:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['01'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_SET:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['41'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_CLEAR:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['02'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_CLEAR_CHECK:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['87'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_GET_SETTING:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['03'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['81'])
        if commandType == SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR_CHECK:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['88'])
        if commandType == SEND_COMMAND_TYPE_ONLINE_GET:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['07'])
        if commandType == SEND_COMMAND_TYPE_ONLINE_SET:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['46'])
        if commandType == SEND_COMMAND_TYPE_ONLINE_SET_WORK:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['47'])
        if commandType == SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['86'])
        if commandType == SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR_CHECK:
            return HtRecord(ht_code=0x0aa0, item_length=2, items=['89'])

    def __compose_codes(self, commandCodes):
        # this done becaue of an asymetry between HtRecords which reflect command codes as integers
        # and various calls to sendHtCommand that supply command codes as both hex strings  and integers
        commandCodes = ["%04X" % c if type(c) is int else c for c in commandCodes]
        return HtRecord(ht_code=0x0a1a, item_length=4, items=commandCodes)

    def __compose_items(self, ht_code, records):
        return HtRecord(ht_code=int(f"0x{ht_code}", 16), item_length=len(records[0]), items=records)

    def __command_codes_required(self, commandType):
        return commandType in [SEND_COMMAND_TYPE_OFFLINE_GET,
                               SEND_COMMAND_TYPE_OFFLINE_CLEAR,
                               SEND_COMMAND_TYPE_OFFLINE_GET_SETTING,
                               SEND_COMMAND_TYPE_OFFLINE_SET,
                               SEND_COMMAND_TYPE_ONLINE_GET,
                               SEND_COMMAND_TYPE_ONLINE_SET,
                               SEND_COMMAND_TYPE_ONLINE_SET_WORK,
                               SEND_COMMAND_TYPE_ONLINE,
                               SEND_COMMAND_TYPE_OFFLINE
                               ]

    def sendHtCommand(self, commandCodes, commandType=SEND_COMMAND_TYPE_OFFLINE_GET, records: HtRecord = None):

        if not commandCodes and self.__command_codes_required(commandType=commandType):
            raise ValueError("Missing HT command code(s)")

        # Command that tells HT whether you want to read or write
        ht_records = [
            self.__compose_command(commandType)
        ]

        if commandType in [SEND_COMMAND_TYPE_OFFLINE_GET,
                           SEND_COMMAND_TYPE_ONLINE_GET,
                           SEND_COMMAND_TYPE_OFFLINE_CLEAR,
                           SEND_COMMAND_TYPE_OFFLINE_CLEAR_CHECK]:
            # List of HT codes you want to read
            ht_records.append(self.__compose_codes(commandCodes))
            return self.__htAdaptor.sendRecords(records=ht_records)

        elif commandType in [SEND_COMMAND_TYPE_OFFLINE_SET, SEND_COMMAND_TYPE_ONLINE_SET]:
            # List of HT records you want to write
            if records:
                return self.__htAdaptor.sendRecords(records=ht_records,
                                                    data_record=self.__compose_items(commandCodes[0], records))
            else:
                raise ValueError("Missing HT records to write")
