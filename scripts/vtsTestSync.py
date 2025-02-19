#! /usr/bin/env python3
import argparse
import time
import statistics
from analog import *
from framework import *


class VtsTestSync():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework

    def fix_to_uut_readback(self, active: bool):
        self.__framework.fixtureSyncWrite(active)

        self.__framework.pause()
        result = self.__framework.consoleSend(command="test_vts sync read")
        return result[0]

    def uut_to_fix_readback(self, active: bool):
        self.__framework.consoleSend(command=f"test_vts sync {'low' if active else 'high'}")

        self.__framework.pause()
        state = self.__framework.fixtureSyncRead()
        adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseVtSync, size=10)
        avgVolts = statistics.mean(adcData)
        return state, avgVolts

    def run(self):
        self.__framework.start("VTS Sync read write")

        # setup mux for
        #       None
        self.__framework.fixtureSetMux(InputMux.NoConnect, OutputMux.NoConnect)
        self.__framework.fixtureSerialReset()
        self.__framework.consoleSend(command="test_vts reset")
        self.__framework.consoleSend(command="test_vts passthrough off")

        uut_reads = []
        for i in range (3):
            readback = self.fix_to_uut_readback((i % 2) != 0)
            uut_reads.append(readback)

        expected = [
            'sync=high',
            'sync=low',
            'sync=high',
        ]
        self.__framework.addResult(name="VTS Sync Fixture writes UUT read backs",
                                   result=(uut_reads == expected))

        fix_reads = []
        sync_volts = []
        for i in range (3):
            state, avgVolts = self.uut_to_fix_readback((i % 2) != 0)
            fix_reads.append(state)
            sync_volts.append(avgVolts)

        expected = [1, 0, 1]

        self.__framework.addResult(name="VTS Sync Fixture reads back UUT writes",
                                   result=(fix_reads == expected))

        expected = [1, 0, 2]
        classed_voltages = AnalogData.clasifyAnalogData(sync_volts, [0.3, 10])
        self.__framework.addResult(name="VTS Sync Fixture voltage checks of UUT writes",
                                   result=(classed_voltages == expected))


if __name__ == "__main__":
    parser = TestArguments("VtsTestSync")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        test = VtsTestSync(framework)
        test.run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
