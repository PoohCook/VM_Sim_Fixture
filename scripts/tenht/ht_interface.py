from typing import Callable, Tuple, Any, List
from .record import HtRecord

SEND_COMMAND_TYPE_OFFLINE_GET = "htOfflineGet"
SEND_COMMAND_TYPE_OFFLINE_CLEAR = "htOfflineClear"
SEND_COMMAND_TYPE_OFFLINE_GET_SETTING = "htOfflineGetSetting"
SEND_COMMAND_TYPE_OFFLINE_SET = "htOfflineSet"
SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR = "htOfflineAllClear"
SEND_COMMAND_TYPE_OFFLINE_CLEAR_CHECK = "htOfflineClearCheck"
SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR_CHECK = "htOfflineAllClearCheck"
SEND_COMMAND_TYPE_ONLINE_GET = "htOnlineGet"
SEND_COMMAND_TYPE_ONLINE_SET = "htOnlineSet"
SEND_COMMAND_TYPE_ONLINE_SET_WORK = "htOnlineSetWork"
SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR = "htOnlineAllClear"
SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR_CHECK = "htOnlineAllClearCheck"
SEND_COMMAND_TYPE_ONLINE = SEND_COMMAND_TYPE_ONLINE_GET
SEND_COMMAND_TYPE_OFFLINE = SEND_COMMAND_TYPE_OFFLINE_GET


class HtGenericError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HtFailedCredentials(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HtInterface():
    def sendHtCommand(self, commandCodes, commandType=SEND_COMMAND_TYPE_OFFLINE_GET, records=None):
        '''Issue HT commands via BeaconService

        @commandCodes   An array of 4-byte strings that each represent a command code. (e.g. ["0BC0", "0BB1"])
                     only the first command code will be used for HT SET command types
        @commandType    This represents the HT command type. Valid values are:
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_GET
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_CLEAR
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_GET_SETTING
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_SET
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_CLEAR_CHECK
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_ALL_CLEAR_CHECK
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_GET
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_SET
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_SET_WORK
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR
                     - EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_ALL_CLEAR_CHECK
                     The default value is EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_GET
        @records        An array of equal-length strings that represents each item payload of the HT command.
                     This is only needed for EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_OFFLINE_SET
                     and EXT_SERVICE_ARGUMENT_HT_SEND_COMMAND_TYPE_ONLINE_SET

        @return none
        '''
        return self.send_sync.sendHtCommand(commandCodes=commandCodes, commandType=commandType, records=records)

    def onHTResponseUpdate(self, frame: int, last: bool, response: int, data: bytearray,
                           datalength: int, itemlength: int, recipient: str) -> None:
        '''Depricated: Called to update the extension service with new HT Responses received from the Master Controller

        this callback is sent to an extension service if HT updates have been requested. It is sent whenever
        HT Responses from the Master Controller have been received.

        @frame           integer number of the frame that the response came from
        @last            boolean True if this is the last response in the frame, false if more to come
        @response        integer response code (unsigned 16 bit)  of the response received
        @data            array of counter strings associated with the response
        @datalength      size/length of the data buffer
        @itemlength      size/length of each item in the data buffer
        @recipient       string representation of the target recepient of the command.
                        "beacon" if BeaconService is the recipient, "ht" if the real HT is the recipient,
                        or the extCode from sendHtCommand()
        '''
        self.send_async.onHTResponseUpdate(frame=frame, last=last, response=response, data=data,
                                                  datalength=datalength, itemlength=itemlength, recipient=recipient)

    def onHTRecordsUpdate(self, origin: str, records: List[HtRecord]) -> None:
        '''Called to update extension services with new HT Record Updates

        this callback is sent to an extension service if HT updates have been recieved.

        @origin          string value of either "IR" or "MC"
        @records         list of HtRecord objects
        '''
        self.send_async.onHTRecordsUpdate(origin=origin, records=records)

    def onHTCommandUpdate(self, frame, last, command, data, datalength, itemlength):
        '''Called to update the extension service with new HT commands that were received from the Handy Terminal

        this callback is sent to an extension service if HT updates have been requested. It is sent whenever
        HT Commands from the Handy Terminal have been received.

        @param frame           integer number of the frame that the command came from
        @param last            boolean True if this is the last command in the frame, false if more to come
        @param command         integer command code (unsigned 16 bit)  of the command received
        @param data            bytearray of data associated with the command
        @param datalength      size/length of the data buffer
        @param itemlength      size/length of each item in the data buffer
        '''
        self.send_async.onHTCommandUpdate(frame=frame, last=last, command=command,
                                          data=data, datalength=datalength, itemlength=itemlength)
