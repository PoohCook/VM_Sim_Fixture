#! /usr/bin/env python3
import argparse
import time
import statistics
from analog import *
from framework import *


class LedTest():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework

    def run(self):
        self.__framework.start("LED Test")

        # TODO: Use test_white when implementd (SB-2725)
        self.__framework.consoleSend(command="announce test_white", expect_ok=False)

        time.sleep(1.0)
        adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseLedPow, size=120, scale=2)
        classes = AnalogData.clasifyAnalogData(adcData, [4.5])
        self.__framework.addStepNote(f"Driver Voltage Classes: {classes}")

        self.__framework.addResult(name="LED Power check",
                                   result=(classes[0] == 0))

        self.__framework.consoleSend(command="announce off", expect_ok=False)

        states = [
            ['test_red', DriverStatus.DriverStatusRed.value, "RED"],
            # ['test_yellow', DriverStatus.DriverStatusRed.value + DriverStatus.DriverStatusGreen.value, "YELLOW"],
            ['test_green', DriverStatus.DriverStatusGreen.value, "GREEN"],
            # ['test_cyan', DriverStatus.DriverStatusGreen.value + DriverStatus.DriverStatusBlue.value, "CYAN"],
            ['test_blue', DriverStatus.DriverStatusBlue.value, "BLUE"],
            # ['test_magenta', DriverStatus.DriverStatusBlue.value + DriverStatus.DriverStatusRed.value, "MAGENTA"]
        ]

        for state in states:
            self.__framework.consoleSend(command=f"announce {state[0]}", expect_ok=False)

            # TODO: reinstate this test when Fixture can support monitoring LED drivers (SB-2727)
            # status = self.__framework.fixtureLedDriverStatus()
            # if status != state[1]:
            #     print(status, state[1])
            #     self.__framework.addStepNote(f"Failed Driver check: {state[0]}")
            #     passed = False

            result = self.__framework.fixturePromptUser(prompt=f"Does fixture light show {state[2]}",
                                                        info=f"Fixture light {state[2]}")
            self.__framework.addResult(name=f"{state[2]} LED Driver test",
                                       result=result)

        self.__framework.consoleSend(command=f"announce off", expect_ok=False)


if __name__ == "__main__":
    parser = TestArguments("VtsTestMiso")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        test = LedTest(framework)
        test.run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
