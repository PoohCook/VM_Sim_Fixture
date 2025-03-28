#! /usr/bin/env python3
from collections.abc import Sequence
import json
import os
import sys
from fixture import *
from console import *
from hexCodec import *
from analog import *
from datetime import datetime
from argparse import ArgumentParser, RawTextHelpFormatter


class TestArguments(ArgumentParser):
    def __init__(self, description: str = None, parents: Sequence[ArgumentParser] = None) -> None:
        super().__init__(description=description,
                         formatter_class=RawTextHelpFormatter,
                         parents=parents if parents else [])

        self.add_argument('-a', '--test_parameters', type=str, help='path to Test Parameter cfg')  # noqa
        self.add_argument('-f', '--fixture_device', type=str, help='path to serial device')  # noqa
        self.add_argument('-c', '--console_device', type=str, help='path to console serial device')  # noqa
        self.add_argument('-r', '--run_cycles', type=int, default=1, help="Number of cycles to run test")
        self.add_argument('-l', "--logout", action='store_true', help="Force logout when done")
        self.add_argument('-s', '--serial_number', type=str, help='specify serial number ot set if test passes')  # noqa
        self.add_argument('-p', "--power_cycle", action='store_true', help="Force Cycle of UUT Power")
        self.add_argument('-o', '--operator_prompt', action='store_true', help="Use operator prompts for confirm")
        self.add_argument('-x', '--power_off', action='store_true', help="Kill the UUT power")
        self.add_argument('-m', '--max_bias', type=int, default=5000, help="Max bias to run in mV")
        self.add_argument('-n', '--min_bias', type=int, default=0, help="Min bias to run in mV")
        self.add_argument('-b', '--bias_step', type=int, default=500, help="Bias step by x mv")
        self.add_argument('-u', '--uut_user', type=str, help='specify user name to login on uut')  # noqa
        self.add_argument('-w', '--uut_password', type=str, help='specify password to login on uut')  # noqa


class TestRecord():
    def __init__(self, name, mute_std = False ) -> None:
        self.name = name
        self.mute_std = mute_std
        self.steps = []
        self.results = {}

    def getLeader(self):
        time = datetime.now()
        return f"{datetime.strftime(time, '%Y-%m-%d %H:%M:%S')}:{int(time.microsecond/1000):03d}"

    def addStep(self, step):
        msg = f"{self.getLeader()}: {step}"
        if not self.mute_std:
            print(msg)
        self.steps.append(msg)

    def addBreak(self):
        if not self.mute_std:
            print("____________________")

    def addResult(self, name, result):
        self.results[name] = {
            "result": result
        }
        if not self.mute_std:
            if result:
                print(f"{self.getLeader()}: [{name}]: passed")
            else:
                print(f"{self.getLeader()}: [{name}]: FAILED!")
            self.addBreak()

    def passed(self):
        return all(v['result'] for v in self.results.values())

    def __repr__(self) -> str:
        overall = "passed" if self.passed() else "Failed!"
        print("__________________________________________________________________________")
        report = [f"[{k}]: {'passed' if v['result'] else 'Failed' }" for k, v in self.results.items()]
        return "\n    ".join([f"{self.name}: {overall}"] + report)


class TestFramework():
    diff_offest = 1650

    def __init__(self, fixture_device: str = None, console_device: str = None, args=None, spinup: bool = True) -> None:
        if args is None and (fixture_device is None or console_device is None):
            raise ValueError(f"Framework requires either fixture_device and console_device or TestArguments")

        self.args = args
        self.parameters = None
        self.load_parameters(args)

        if self.args and self.args.serial_number:
            self.__validate_serial_number(self.args.serial_number)

        if not fixture_device:
            fixture_device = args.fixture_device
        if not console_device:
            console_device = args.console_device

        self.__start_test = datetime.now()
        self.__records = []
        self.__record = None
        self.__fixture_port = FixturePort(device=fixture_device)
        self.__fixture_port.flush()
        self.__console_port = None
        self.__console_device = console_device
        self.__record = TestRecord(name="Framework")

        fixture_version = self.fixtureVersion()
        require = self.getParameter("enforcements.fixture_version")
        if require and fixture_version != require:
            raise ValueError(f"Required Fixture Version {require} does not match current version {fixture_version}")

        self.__spinup = spinup
        if spinup:
            self.spinupUut()

    def getParameter(self, path):
        parts = path.split('.')
        current = self.parameters
        for part in parts:
            if type(current) is not dict:
                return None
            if part not in current:
                return None
            current = current[part]

        return current

    def load_parameters(self, args):
        if args.test_parameters:
            if not os.path.exists(args.test_parameters):
                raise ValueError(f"Cannot locate specified TestParameters file: {args.test_parameters}")
            with open(args.test_parameters, "r") as f:
                self.parameters = json.load(f)
            if "arguments" in self.parameters:
                for key, val in self.parameters["arguments"].items():
                    if self.args.__dict__.get(key) is None:
                        self.args.__dict__[key] = val

    def spinupUut(self):
        self.powerSetup(on=True, cycle=self.args.power_cycle)
        self.addStepNote(f"UUT connecting")
        self.__console_port = ConsolePort(device=self.__console_device, record=self.__record, diagnostics=False)
        self.__console_port.connect(self.args.uut_user, self.args.uut_password)
        self.addStepNote(f"UUT Connection completed")
        self.consoleSend(command="test_scan configed false fixture false")
        self.consoleSend(command="announce off", expect_ok=False)
        version = self.displayUutVersion()

        require = self.getParameter("enforcements.sb4_firmware_version")
        if require and require != version["firmwareVersion"]:
            raise ValueError(f"Required SB4 Firmware Version {require} does not match current version {version['firmwareVersion']}")  # noqa

        require = self.getParameter("enforcements.stm_firmware_version")
        if require and require != version["stmFirmwareVersion"]:
            raise ValueError(f"Required STM Firmware Version {require} does not match current version {version['stmFirmwareVersion']}")  # noqa

        time.sleep(2.0)  # just a little bit to settle in

    def powerSetup(self, on: bool = True, cycle: bool = False):
        if cycle:
            self.addStepNote(f"UUT Power Cycling")
            self.fixtureUutPower(False)
            time.sleep(1.0)

        self.fixtureUutPower(on)
        if cycle:
            time.sleep(2)

    def start(self, test_name, mute_std = False):
        self.__record = TestRecord(name=test_name, mute_std=mute_std)
        self.__records.append(self.__record)
        self.__record.addBreak()
        self.addStepNote(f"Start: {test_name}")

    def shutdown(self):
        self.fixtureSetMux(InputMux.NoConnect, OutputMux.NoConnect)
        if self.__console_port:
            if self.args.logout:
                self.__console_port.disconnect()
            self.__console_port.close()
        end_test = datetime.now()
        duration = end_test - self.__start_test
        if self.args.power_off and self.__spinup:
            self.powerSetup(on=False)
        self.__fixture_port.close()
        self.addStepNote(f"elapsed time: {duration.total_seconds():.2f} sec")

    def run(self, test_func):
        for i in range(self.args.run_cycles):
            if i > 0 and self.args.power_cycle:
                self.spinupUut()
            test_func()

    def fixtureVersion(self):
        packet = Packet(command=Command.VersionRead)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to reset serial: {response}")
        version = ".".join([f'{d}' for d in response.data])
        self.addStepNote(f"Fixture Version: {version}")
        return version

    def fixtureUutPower(self, on: bool):
        self.addStepNote(f"Fixture UUT Power: {'on' if on else 'off'}")
        packet = Packet(command=Command.UutPower, data=[on])
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to set UUT Power: {response}")

    def fixtureSetMux(self, input_mux: InputMux, output_mux: OutputMux):
        self.addStepNote(f"Fixture: Setup Mux(input={input_mux.name}, output={output_mux.name}")
        packet = Packet(command=Command.SetupMux, data=[input_mux.value, output_mux.value])
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to setup mux: {response}")

    def fixtureSerialReset(self):
        self.addStepNote("Fixture: Clear Serial RX")
        packet = Packet(command=Command.SerialReset)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to reset serial: {response}")

    def fixtureSerialSendData(self, data: str, wait: bool = True):
        self.addStepNote(f"Fixture: Send Data: {data}")
        command = Command.SerialSend if wait else Command.SerialSendNoWait
        packet = Packet(command=command, data=HexCodec.decodeDataStr(data))
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to send serial data: {response}")

    def fixtureSerialRead(self, size: int, expect_ack: bool = True):
        self.addStepNote(f"Fixture: Read Data({size})")
        packet = Packet(command=Command.SerialRead, data=[size])
        response = self.__fixture_port.send(packet=packet, timeout=3.0)
        if expect_ack and response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to fetch serial data: {response}")
        data = HexCodec.encodeDataStr(response.data)
        self.addStepNote(f"       <= {data})")
        return data

    def fixtureSerialSendComRequest(self):
        self.addStepNote("Fixture: Send Serial Com request")
        packet = Packet(command=Command.SerialSendComRequest)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to send com request: {response}")

    def fixtureSerialSendWaitComRequest(self):
        self.addStepNote("Fixture: Send Serial Wait Com request")
        packet = Packet(command=Command.SerialWaitComRequest)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to setup com request wait: {response}")

        packet = None
        while packet is None or packet.command != Command.SerialComReqDetected:
            packet = self.__fixture_port.read_packet(timeout=30.0)
        return True


    def getKeyboardChar(self):
        try:
            # Check if the platform is Windows
            if sys.platform == 'win32':
                import msvcrt
                return msvcrt.getch().decode('utf-8')
            else:
                # For Unix-based systems (Linux, macOS)
                import termios
                import tty

                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)

                try:
                    tty.setraw(fd)
                    return sys.stdin.read(1)

                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except KeyboardInterrupt:
            pass

    def fixturePromptUser(self, prompt, info):
        if self.args.operator_prompt:
            for i in range(3):
                self.addStepNote(f"Prompt: {prompt}? (y/n))")
                opKey = self.getKeyboardChar()
                if opKey in ["y", "Y"]:
                    return True
                if opKey in ["n", "N"]:
                    return False
                self.addStepNote(f"Invalid key! Must be y or n")

            return False
        else:
            self.addStepNote(f"Fixture: {info}")
            time.sleep(1)
        return True

    def __getTimeoutMsecData(self, timeout):
        # timeout for fixtue command is int number of msec as little Endian 2 byte
        if not (0 <= timeout <= 60.0):
            raise ValueError(f"Invalid timeout: {timeout}")
        msecs = int(timeout / 0.001)
        return [msecs & 0xff, (msecs & 0xff00) >> 8]

    def fixtureAdcReadData(self, channel: SenseChannel, size: int, scale: int = 4, magnitude: int = 1000,
                           trigger: TriggerSource = TriggerSource.TriggerSoftware, getRaw=False, timeout=1.0):
        self.addStepNote(f"Fixture: Read Adc Data: chan={channel.name}, size={size}, trigger={trigger.name}")

        packet = Packet(command=Command.AdcRead,
                        data=[channel.value, size, trigger.value] + self.__getTimeoutMsecData(timeout))
        response = self.__fixture_port.send(packet=packet, timeout=timeout + 0.2)
        diff_mv = self.diff_offest if channel == SenseChannel.SenseIeDiff else 0
        adcData = AnalogData.decodeByteData(response.data, scale=scale, magnitude=magnitude,
                                            getRaw=getRaw, diff_mv=diff_mv)
        self.addStepNote(f"       <= {adcData})")
        return adcData

    def fixtureSetDacValue(self, channel: DacChannel, value_mv: int):
        self.addStepNote(f"Fixture: Write DAC value: chan={channel.name}, value={value_mv}")
        packet = Packet(command=Command.DacWrite, data=[channel.value, value_mv & 0xff, (value_mv & 0xff00) >> 8])
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to set DAC value: {response}")

    def fixtureSyncWrite(self, active: bool):
        self.addStepNote(f"Fixture: Write VTS Sync active: {active}")
        packet = Packet(command=Command.SyncWrite, data=[active & 0xff])
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to set sync value: {response}")

    def fixtureSyncRead(self):
        self.addStepNote(f"Fixture: Read VTS Sync")
        packet = Packet(command=Command.SyncRead)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to read sync value: {response}")
        self.addStepNote(f"       <= {response.data[0]})")
        return response.data[0]

    def fixtureLedDriverStatus(self):
        self.addStepNote(f"Fixture: Read Led Driver Status")
        packet = Packet(command=Command.LedStatus)
        response = self.__fixture_port.send(packet=packet)
        if response.command != Command.Ack:
            raise RuntimeError(f"Fixture unable to read sync value: {response}")
        self.addStepNote(f"       <= 0x{response.data[0]:02x})")
        return response.data[0]

    def displayUutVersion(self):
        version_info = self.consoleVersion()
        fmt_info = '\n'.join(version_info)
        self.addStepNote(f"UUT Version:\n{fmt_info}")
        splits = [line.split(':', maxsplit=1) for line in version_info]
        return {info[0].strip(): info[1].strip() for info in splits}

    def consoleVersion(self):
        command = "version"
        return self.__console_port.send_to_console(command, timeout=1.0, expect_ok=False)

    def consoleSend(self, command, expect_ok: bool = True):
        self.addStepNote(f"UUT: => {command}")
        timeout = 1.0 if expect_ok else 0.3
        result = self.__console_port.send_to_console(command, timeout=timeout, expect_ok=expect_ok)
        if expect_ok and "OK" not in result:
            raise RuntimeError(f"Failed ({command}): {result}")
        self.addStepNote(f"    <= {result}")
        return result

    def consoleSendNoWait(self, command):
        self.addStepNote(f"UUT: => {command}")
        result = self.__console_port.send_command(command)

    def consoleGetResult(self, expect_ok: bool = True):
        result = self.__console_port.send_to_console(None, expect_ok=expect_ok)
        if expect_ok and "OK" not in result:
            raise RuntimeError(f"Failed (getResult): {result}")
        self.addStepNote(f"    <= {result}")
        return result

    def addStepNote(self, note):
        self.__record.addStep(note)

    def pause(self):
        time.sleep(0.12)

    def addResult(self, name, result):
        self.__record.addResult(name=name, result=result)

    def report(self):
        passed = 0
        failed = 0
        for record in self.__records:
            print(record)
            print("")
            if record.passed():
                passed += 1
            else:
                failed += 1

        print("----------------------------")
        if failed == 0:
            print(f"Ran {len(self.__records)} tests: All Passed")
        else:
            print(f"Ran {len(self.__records)} tests: {passed} Passed and {failed} Failed!")
        print("")

        if failed == 0 and self.args and self.args.serial_number:
            self.addStepNote(f"Setting Beacon Serial Number: {self.args.serial_number}")
            self.consoleSend(command=f"test_set_serial override num {self.args.serial_number}")

        self.displayUutVersion()
        self.consoleSend(command=f"announce {'test_green' if failed == 0 else 'test_red'}", expect_ok=False)

    def __validate_serial_number(self, serial_num):
        match = re.match(r'SBE([0-9]{3})-M[012]{1}-([0-9]{4})[0-9]{5}', serial_num)
        if not match:
            raise ValueError(f"Invalid serial number: {serial_num}. Must be SBExxx-Mx-xxxxxxxxx")
        if match.group(1)[0] != '4':
            raise ValueError(f"Invalid serial number: {serial_num}. series number must be 4xx")
        current = datetime.now()
        cur_date = current.strftime("%y%m")
        if cur_date != match.group(2):
            raise ValueError(f"Invalid serial number: {serial_num}. date does not match today")


def parseData(line):
    parts = line.split("data:")
    if len(parts) != 2:
        return "[]"
    return parts[1][:-1]


if __name__ == "__main__":
    parser = TestArguments("Framework")
    args = parser.parse_args()
    framework = TestFramework(args=args, spinup=False)

    if args.power_off:
        framework.powerSetup(on=False)
    else:
        framework.powerSetup(on=True)

    framework.shutdown()
