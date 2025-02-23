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


HT_STATE_REST = 0
HT_STATE_AWAIT_SEND_MODE = 1
HT_STATE_AWAIT_CREQ_ACK = 2
HT_STATE_AWAIT_ACK = 3
HT_STATE_AWAIT_DATA = 4
HT_STATE_FAILED_CREDENTIALS = 5
HT_STATE_FAILED_RECORDS = 6

HT_RETRIES = 3
HT_SEND_TIMEOUT = 3
HT_STATE_TIMEOUT = 1.0
HT_SEND_GRANULAR = 100


class HtRecordsPhase(Enum):
    CREDENTIALS = 1
    COMMAND = 2
    RECORDS = 3


class TenHtAdaptor():
    ORIGIN_IR = "IR"
    ORIGIN_MC = "MC"

    def __init__(self,
                 extension: HtBase,
                 monitorHandler: Callable[[str, List[HtRecord]], None] = None,
                 commandHandler: Callable[[List[HtRecord]], None] = None) -> None:

        self._htExt = extension
        self.__pending_htConfig = None
        self.__pending_htRecord: List[HtRecord] = None
        self.__record_codec = HtRecordCodec()
        self.__response_handler = None
        self.__ht_records_phase = None
        self.__htContinuedFrame = False
        self.__state = HT_STATE_REST
        self.__state_begin = datetime.now()
        self.__retry_func = None
        self.__retry_count = HT_RETRIES
        self.__rcv_frames = []
        self.__current_send_frames = None
        self.__read_mode = True

        self._monitorHandler = monitorHandler
        self._commandHandler = commandHandler
        self._config_args = {}

    def onConfigure(self, args):
        try:
            self._config_args = args
            self.__record_codec.set_htConfig(self.getHtConfig())
        except Exception as e:
            logging.warning(f"Exception encountered while setting htConfig: {e}")

    def onConfigUpdate(self, path, value):
        if path == "Beacon.htConfig":
            try:
                self.__record_codec.set_htConfig(htConfig=value)
            except Exception as e:
                logging.warning(f"Exception encountered while updating htConfig: {e}")

    def onStart(self):
        self._htExt.addIoFrameListener(TenIoListener("HtListener", self.__feed_rcv_frame, interest=[HtGenericFrame]))

    def getHtConfig(self):
        return self._config_args.get("htConfig", "")

    def __feed_rcv_frame(self, frame: HtGenericFrame):
        if type(frame) is HtPassthroughModeFrame:
            self.__handle_passthrough()
        elif type(frame) is HtSendModeFrame:
            self.__handle_send_mode()
        elif type(frame) is HtComRequestFrame:
            self.__ht_records_phase = HtRecordsPhase.CREDENTIALS
        elif isinstance(frame, HtDataFrame):
            self.__handle_data_frame(frame)

    def __handle_passthrough(self):
        if self.__state == HT_STATE_AWAIT_SEND_MODE:
            self._retry_frame(HtSendModeFrame())

    def __handle_send_mode(self):
        if self.__state == HT_STATE_AWAIT_SEND_MODE:
            self.__dispatch_with_retry(retry_func=self.__dispatch_com_req)

    def __handle_ack_nak(self, frame):
        is_ack = frame.data[0] == ACK1
        if self.__state == HT_STATE_AWAIT_CREQ_ACK:
            if not is_ack:
                self._retry_frame(HtComRequestFrame())
                return
            self.__dispatch_with_retry(retry_func=self.__send_next_frames)
            return

        if self.__pending_htConfig:
            if is_ack:
                logging.info("HtConfig updated to: %s", self.__pending_htConfig)
                self._htExt.setConfigValue(path="Beacon.htConfig", value=self.__pending_htConfig)
            else:
                logging.info("HtConfig reverted to: %s", self.getHtConfig())
                self.__record_codec.set_htConfig(self.getHtConfig())
            self.__pending_htConfig = None

        if self.__state == HT_STATE_AWAIT_ACK:
            if not is_ack:
                if self.__ht_records_phase == HtRecordsPhase.CREDENTIALS:
                    self.__dispatch_with_retry(retry_func=self.__dispatch_com_req)
                    self._process_retries()
                else:
                    self._retry_frame(self.__current_send_frames[0])
                return

            if self.__current_send_frames:
                if self.__ht_records_phase == HtRecordsPhase.CREDENTIALS:
                    self.__ht_records_phase = HtRecordsPhase.RECORDS
                else:
                    self.__retry_count = HT_RETRIES
                next_frame = len(self.__current_send_frames)
                for i, frame in enumerate(self.__current_send_frames):
                    if frame.is_end:
                        next_frame = i + 1
                        break
                self.__current_send_frames = self.__current_send_frames[next_frame:]
                if self.__current_send_frames:
                    self.__dispatch_with_retry(retry_func=self.__send_next_frames)
                else:
                    if self.__pending_htRecord:
                        logging.info(f"HtRecord updated: {format(self.__pending_htRecord[0].ht_code, '04x')}")
                        if self._monitorHandler:
                            origin = TenHtAdaptor.ORIGIN_MC if type(frame) is HtMcFrame else TenHtAdaptor.ORIGIN_IR
                            self._monitorHandler(origin, self.__pending_htRecord)
                    self.__pending_htRecord = None

    def __handle_data_frame(self, frame: HtDataFrame):
        if len(frame.data) == 1 and not self.__htContinuedFrame:
            self.__handle_ack_nak(frame)
            return

        if not self.__htContinuedFrame:
            self.__rcv_frames = [frame]
        else:
            self.__rcv_frames.append(frame)

        self.__htContinuedFrame = not frame.is_end
        if frame.is_end:
            origin = TenHtAdaptor.ORIGIN_MC if type(frame) is HtMcFrame else TenHtAdaptor.ORIGIN_IR

            if origin == TenHtAdaptor.ORIGIN_IR and self.__ht_records_phase == HtRecordsPhase.CREDENTIALS:
                self.__pending_htConfig = self.__record_codec.update_htConfig(self.__rcv_frames[0])
                self.__ht_records_phase = HtRecordsPhase.COMMAND
                return

            if self.__state != HT_STATE_REST:
                self._htExt.sendIoFrame(HtMcFrame(is_end=True, data=[ACK1]))

            records = self.__record_codec.decodeRecords(self.__rcv_frames)
            if self.__response_handler:
                self.__response_handler(records)
                self.__response_handler = None

            if origin == TenHtAdaptor.ORIGIN_IR and self.__ht_records_phase == HtRecordsPhase.COMMAND:
                self._commandHandler(records)
                self.__ht_records_phase = HtRecordsPhase.RECORDS
                return

            if self._monitorHandler:
                self._monitorHandler(origin, records)

            self.__state = HT_STATE_REST

    def __send_next_frames(self):
        if self.__current_send_frames:
            self.__state = HT_STATE_AWAIT_ACK
            for frame in self.__current_send_frames:
                self._htExt.sendIoFrame(frame)
                if frame.is_end:
                    break
        else:
            if self.__read_mode:
                self.__state = HT_STATE_AWAIT_DATA
            else:
                self.__state = HT_STATE_REST

    def _process_retries(self):
        self.__retry_count -= 1
        if self.__retry_count <= 0:
            logging.error("Failed retry of send frame")
            if self.__ht_records_phase == HtRecordsPhase.CREDENTIALS:
                self.__state = HT_STATE_FAILED_CREDENTIALS
            else:
                self.__state = HT_STATE_FAILED_RECORDS
            return

    def _retry_frame(self, frame: HtGenericFrame):
        self._process_retries()
        self._htExt.sendIoFrame(frame)

    def __dispatch_with_retry(self, retry_func):
        self.__state_begin = datetime.now()
        self.__retry_func = retry_func
        self.__retry_func()

    def __dispatch_send_mode(self):
        self.__state = HT_STATE_AWAIT_SEND_MODE
        self._htExt.sendIoFrame(HtSendModeFrame())

    def __dispatch_com_req(self):
        self.__state = HT_STATE_AWAIT_CREQ_ACK
        self._htExt.sendIoFrame(HtComRequestFrame())
        self.__ht_records_phase = HtRecordsPhase.CREDENTIALS

    def sendRecords(self, records: List[HtRecord], response_handler: Callable[[List[int]], None] = None,
                    data_record: HtRecord = None):
        if not records:
            raise ValueError("records required to send")

        self.__response_handler = response_handler
        self.__current_send_frames = [
            self.__record_codec.getCredentialsFrame(),
            *self.__record_codec.encodeRecords(records)
        ]
        self.__read_mode = data_record is None
        if data_record:
            self.__current_send_frames += self.__record_codec.encodeRecords([data_record])
            self.__pending_htRecord = [data_record]

        self.__dispatch_with_retry(retry_func=self.__dispatch_send_mode)

        self.__retry_count = HT_RETRIES
        start = datetime.now()
        for i in range((HT_SEND_TIMEOUT + 1) * HT_SEND_GRANULAR):
            if self.__state == HT_STATE_REST:
                return
            elif self.__state == HT_STATE_FAILED_CREDENTIALS:
                self.__state = HT_STATE_REST
                raise HtFailedCredentials("failed to acknowledge credentials")
            elif self.__state == HT_STATE_FAILED_RECORDS:
                self.__state = HT_STATE_REST
                raise HtGenericError("failed to acknowledge record")

            current_time = datetime.now()
            if (current_time - self.__state_begin).total_seconds() > HT_STATE_TIMEOUT:
                self.__retry_func()
                start = self.__state_begin = datetime.now()

            if (current_time - start).total_seconds() > HT_SEND_TIMEOUT:
                self.__state = HT_STATE_REST
                break
            time.sleep(1.0 / HT_SEND_GRANULAR)
        raise HtGenericError("timed out sending HT records")
