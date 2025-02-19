#! /usr/bin/env python3
import argparse
import serial
import time
import re
from hexCodec import *
from typing import List
from collections.abc import Iterable
from enum import Enum
from datetime import datetime, timedelta


class StateResponses(Enum):
    LoggedOut = "mdm9607-perf login: "
    Password = "Password: "
    LoggedIn = "root@mdm9607-perf:~# "
    Connected = "SB4: "
    Unknown = None


class ConsolePort():
    str_to_par_dict = {
        "even": serial.PARITY_EVEN,
        "odd": serial.PARITY_ODD,
        "none": serial.PARITY_NONE
    }

    def __init__(self, device, baud=115200, parity="none", diagnostics=False, record=None) -> None:
        parity = self.str_to_par_dict.get(parity, serial.PARITY_EVEN)
        self.__port = serial.Serial(port=device, baudrate=baud, parity=parity, timeout=3.0,
                                    rtscts=False, dsrdtr=False, xonxoff=False)

        self.__diagnostics = diagnostics
        self.__record = record
        self.__current_state = StateResponses.Unknown
        self.connected = False

    def __record_step(self, step):
        if self.__record:
            self.__record.addStep(step)

    def check_response_state(self, response):
        cues = [s.value for s in StateResponses if s.value is not None]
        state = StateResponses.Unknown
        for cue in cues:
            if cue in response:
                state = StateResponses(cue)
                break

        if state == StateResponses.Unknown:
            if self.__diagnostics:
                print(f":: {response}")
            else:
                print('.', end="", flush=True)
        elif self.__current_state == StateResponses.Unknown:
            if not self.__diagnostics:
                print("")

        self.__current_state = state
        return state

    def get_state(self) -> StateResponses:
        while True:
            response = self.read_line()
            if response is None:
                return StateResponses.Unknown

            state = self.check_response_state(response)
            if state != StateResponses.Unknown:
                return state

    def __get_timeout(self, seconds):
        return datetime.now() + timedelta(seconds=seconds)

    def wait_boot(self, wait_seconds=15):
        self.__record_step(f"Waiting Boot Complete")
        timeout = self.__get_timeout(wait_seconds)

        while timeout > datetime.now():
            response = self.read_line()
            if response:
                timeout = self.__get_timeout(wait_seconds)
                state = self.check_response_state(response)
                if state != StateResponses.Unknown:
                    return state

        return StateResponses.Unknown

    def login(self, user, password, wait_seconds=10):
        self.__record_step(f"Logging In")
        timeout = self.__get_timeout(wait_seconds)

        state = StateResponses.LoggedOut
        while state != StateResponses.LoggedIn:
            if state == StateResponses.LoggedOut:
                self.send_command(user)
            elif state == StateResponses.Password:
                self.send_command(password)

            state = self.get_state()
            if datetime.now() > timeout:
                return StateResponses.Unknown

        return state

    def wait_beacon_service_loaded(self, wait_secs=10):
        self.__record_step(f"Waiting on beacon_service")
        last_secs = 0
        running_secs = self.beacon_service_loaded_seconds()
        timeout = datetime.now() + timedelta(seconds=(wait_secs + 10))
        while running_secs < wait_secs:
            if last_secs != running_secs:
                self.__record_step(f"beacon_service running: {running_secs}")
                last_secs = running_secs
            if datetime.now() > timeout:
                raise RuntimeError(f"Failed to wait for beacon_service to be running {wait_secs}"
                                   f"seconds. running: {running_secs}")
            time.sleep(1.0)
            running_secs = self.beacon_service_loaded_seconds()

        self.__record_step(f"beacon_service running: {running_secs} sec")

    def beacon_service_loaded_seconds(self):
        self.send_command("ps | grep beacon")
        result = self.read_line()
        while "ps | grep beacon" not in result:   # read back sent command and junk
            result = self.read_line()

        result = self.read_line()  # read back first response line
        match = re.search(r'(\d{1,2}:\d{2}) {beacon_service}', result)
        if match:
            self.read_line()       # blow off second response line
            parts = match.group(1).split(':')
            return (int(parts[0]) * 60) + int(parts[1])

        return 0

    def console(self, wait_seconds=30):
        timeout = self.__get_timeout(wait_seconds)
        self.wait_beacon_service_loaded()

        self.__record_step(f"Connecting to console")
        self.send_command("console")
        state = StateResponses.LoggedIn
        while state != StateResponses.Connected:
            state = self.get_state()
            if datetime.now() > timeout:
                return StateResponses.Unknown

        time.sleep(1)
        return state

    def connect(self, user, password):
        self.send_command("")
        state = self.get_state()
        self.__record_step(f"Initial: {state.name}")

        if state == StateResponses.Unknown:
            state = self.wait_boot()
            self.__record_step(f"State: {state.name}")

        if state == StateResponses.LoggedOut:
            state = self.login(user, password)
            self.__record_step(f"State: {state.name}")

        if state == StateResponses.LoggedIn:
            state = self.console()
            self.__record_step(f"State: {state.name}")

        if state == StateResponses.Connected:
            self.connected = True
            self.__record_step(f"State: {state.name}")

        if not self.connected:
            raise RuntimeError(f"Unable to connect: {state}")

    def disconnect(self):
        self.send_command("")
        state = self.get_state()

        if state == StateResponses.Connected:
            self.send_command("quit!")
            while state != StateResponses.LoggedIn:
                state = self.get_state()
            time.sleep(2)

        if state == StateResponses.LoggedIn:
            self.send_command("exit")
            while state != StateResponses.LoggedOut:
                state = self.get_state()

            self.connected = False

        self.__record_step(f"State: {state.name}")

    def send_command(self, command: str) -> None:
        command += '\r\n'
        data = command.encode()
        if self.__diagnostics:
            print(f"=> {data}")
        for c in data:
            self.__port.write(bytes([c]))
            time.sleep(0.0005)

    def send_to_console(self, command: str, timeout=0.5, expect_ok: bool = False) -> List[str]:
        if command:
            self.send_command(command)

        self.__port.timeout = timeout
        results = []

        while True:
            response = self.read_line()
            if response is None:
                break
            response = re.sub(r'SB4:\s+', '', response).strip()
            if response not in [command, ""]:
                results.append(response)
                if expect_ok and response == 'OK':
                    break
            # self.__port.timeout = 0.2

        return results

    def read_line(self):
        try:
            line = b''
            start = datetime.now()
            while (datetime.now() - start).total_seconds() < self.__port.timeout:
                c = self.__port.read()
                if c is None or len(c) == 0:
                    break
                line += c
                if c == b'\n':
                    break
                start = datetime.now()

            if not line:
                return None
            if self.__diagnostics:
                print(f"<=: {line}")
            return re.sub(r'[\r\n]*', '', line.decode())
        except Exception as e:
            print(f"line err: {e}")
            return None

    def close(self):
        self.__port.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Console Port', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--device', type=str, help='path to serial device', default="/dev/tty.usbserial-1410")
    parser.add_argument('-b', '--baud', type=int, help='serial baud rate', default=115200)
    parser.add_argument('-p', '--parity', type=str, help='serial parity', default="none")
    parser.add_argument('-c', '--command', type=str, help=f'command to send')
    parser.add_argument('-u', '--uut_user', type=str, help='specify user name to login on uut')  # noqa
    parser.add_argument('-w', '--uut_password', type=str, help='specify password to login on uut')  # noqa

    args = parser.parse_args()

    port = ConsolePort(device=args.device, baud=args.baud, parity=args.parity)

    port.connect(args.uut_user, args.uut_password)

    results = port.send_to_console("announce connected")
    print(f"annc: {results}")

    results = port.send_to_console("test_scan configed:false")
    print(f"scan: {results}")

    port.disconnect()

    port.close()
