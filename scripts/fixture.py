#! /usr/bin/env python3
import argparse
import serial
import time
from hexCodec import *
from typing import List
from collections.abc import Iterable
from enum import Enum

next_frame_id = 0

class Command(Enum):
    Ping = 1
    Pong = 2
    Ack = 3
    Nak = 4
    VersionRead = 5
    UutPower = 6
    SerialSend = 0x10
    SerialSendNoWait = 0x11
    SerialReset = 0x12
    SerialRead = 0x13
    SerialSendComRequest = 0x14
    SetupMux = 0x20
    SyncWrite = 0x21
    SyncRead = 0x22
    AdcRead = 0x30
    DacWrite = 0x31
    LedStatus = 0x40
    Unknown = 0xff


class OutputMux(Enum):
    HtIrMiso = 0X01
    HtMcMosi = 0X02
    VtsMcMosi = 0X04
    VtsMcMiso = 0X08
    NoConnect = 0


class InputMux(Enum):
    HtIrMosi = 0X01
    HtMcMiso = 0X02
    VtsSlvMosi = 0X04
    VtsMcMiso = 0X08
    NoConnect = 0


class SenseChannel(Enum):
    SenseIeDiff = 3
    SenseLedPow = 5
    SenseVtSync = 6
    SenseHtIrMosi = 10
    SenseHtMcMiso = 11
    SenseVtsSlvMosi = 12
    SenseVtsMcMiso = 15


class TriggerSource(Enum):
    TriggerSoftware = 0
    TriggerIeDetect = 1


class DacChannel(Enum):
    DacChannel1 = 1


class DriverStatus(Enum):
    DriverStatusRed = 0X01
    DriverStatusGreen = 0X02
    DriverStatusBlue = 0X04


class Packet():
    MAX_TX_DATA_LENGTH = 250

    def __init__(self, command: Command = None, data: List[int] = None, frame_id: int = None) -> None:
        # length / comp_len / command / data / lrc ...  at least 5 chars dead time ///
        self.command = command
        self.data = data if data is not None else []
        if frame_id is not None:
            self.frame_id = frame_id
        else:
            self.frame_id = self.get_next_frame_id()

    def get_next_frame_id(self):
        global next_frame_id
        next_frame_id = (next_frame_id + 1) % 256
        return next_frame_id

    def encode(self):
        length = len(self.data) + 3
        if length > self.MAX_TX_DATA_LENGTH:
            raise ValueError("Provided data exceeds ALLOWED LENGTH")

        header = [length, ~length & 0xff, self.command.value, self.frame_id]
        checksum = self.command .value
        checksum ^= self.frame_id
        for d in self.data:
            checksum ^= d

        return header + self.data + [checksum]

    @classmethod
    def decode(cls, input: List[int]):
        if input[0] != (~input[1] & 0xff):
            raise ValueError("invalid start sequence")

        length = input[0]
        if len(input[2:]) != length:
            raise ValueError("invalid sequence length")

        if length > cls.MAX_TX_DATA_LENGTH:
            raise ValueError("Provided input exceeds allowed length")

        checksum = 0
        for d in input[2:]:
            checksum ^= d

        if checksum != 0:
            raise ValueError("invalid checksum")

        return cls(Command(input[2]), input[4:-1], frame_id=input[3])

    def __repr__(self) -> str:
        return f"{self.command.name}:{HexCodec.encodeDataStr(self.data)}"


class FixturePort():
    str_to_par_dict = {
        "even": serial.PARITY_EVEN,
        "odd": serial.PARITY_ODD,
        "none": serial.PARITY_NONE
    }

    def __init__(self, device, baud=19200, parity="even") -> None:
        parity = self.str_to_par_dict.get(parity, serial.PARITY_EVEN)
        self.__port = serial.Serial(port=device, baudrate=baud, parity=parity, timeout=0.5,
                                    rtscts=False, dsrdtr=False, xonxoff=False)

    def send(self, packet: Packet, sync: bool = True, timeout: float = 0.5) -> Packet:
        data = packet.encode()
        for c in data:
            self.__port.write(bytes([c]))
            time.sleep(0.0005)

        if sync:
            return self.read(timeout=timeout)

    def read(self, timeout: float = 0.5) -> Packet:
        self.__port.timeout = timeout
        header = self.__port.read(size=2)
        if len(header) != 2:
            raise ValueError(f"timed out waiting on response")

        if header[0] != (~header[1] & 0xff):
            raise ValueError("invalid response header: {header}")

        input = self.__port.read(size=header[0])
        packet = Packet.decode(header + input)
        return packet

    def close(self):
        self.__port.close()


if __name__ == "__main__":
    commands = "\n    ".join([e.name for e in Command])
    parser = argparse.ArgumentParser(description='Fixture', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--device', type=str, help='path to serial device', default="/dev/tty.usbserial-1410")
    parser.add_argument('-b', '--baud', type=int, help='serial baud rate', default=19200)
    parser.add_argument('-p', '--parity', type=str, help='serial parity', default="even")
    parser.add_argument('-c', '--command', type=str, help=f'command to send:\n    {commands}')
    parser.add_argument('-a', '--data', type=str, help='data to send')
    parser.add_argument('-x', '--repeat', action='store_true', help="repeat send")

    args = parser.parse_args()

    fixture_port = FixturePort(device=args.device, baud=args.baud, parity=args.parity)

    if args.command:
        data = HexCodec.decodeDataStr(args.data)

        while True:
            packet = Packet(command=Command[args.command], data=data)
            print(f"Command: {packet}")

            resp = fixture_port.send(packet=packet)
            print(f"Response: {resp}")

            if not args.repeat:
                break

            time.sleep(0.01)

    fixture_port.close()
