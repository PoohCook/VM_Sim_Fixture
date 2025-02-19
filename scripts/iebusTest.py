#! /usr/bin/env python3
from argparse import ArgumentParser
import time
from analog import *
from framework import *


class IebusTest():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework

    def scanAtVoltage(self, bias):
        self.__framework.fixtureSetDacValue(DacChannel.DacChannel1, int(bias / 2))
        time.sleep(0.2)
        sAddr = f"08{(bias & 0xff):02x}"
        print(f"sAddr = ")
        ie_out = f'broad:no mAddr:0800 sAddr:{sAddr} com:0e data:[30,31,32,33,34]'
        self.__framework.consoleSendNoWait(command=f"test_ie send {ie_out}")

        adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseIeDiff, size=120, scale=2,
                                                        trigger=TriggerSource.TriggerIeDetect, timeout=2.0)

        class_profiles = [
            [400, [-0.4, -0.1]],
            [4600, [-0.6, -0.1]],
            [6000, [-0.4, -0.1]]
        ]

        profile = class_profiles[-1]
        for pr in class_profiles:
            if bias < pr[0]:
                profile = pr[1]
                break

        volt_classes = AnalogData.clasifyAnalogData(adcData, profile)
        passed_voltage = volt_classes[0] > 10 and volt_classes[2] > 10
        self.__framework.addStepNote(f"Voltage Classification: {volt_classes}")

        self.__framework.consoleGetResult()

        self.__framework.pause()
        lines = self.__framework.consoleSend(command=f"test_ie read")
        readbacks = lines[:-1]
        self.__framework.consoleSend(command="test_ie reset")
        expect = [
            f'IebusV2Frame(status:2 broad:False maddr:0800 saddr:{sAddr} con:e data:[30,31,32,33,34])',
            f'IebusV2Frame(status:2 broad:False maddr:0800 saddr:{sAddr} con:e data:[30,31,32,33,34])',
            f'IebusV2Frame(status:2 broad:False maddr:0800 saddr:{sAddr} con:e data:[30,31,32,33,34])',
        ]
        passed_readback = (readbacks == expect)
        self.__framework.addResult(name=f"IE readback and differential range: {bias} mV",
                                   result=(passed_voltage and passed_readback))

    def run(self):
        self.__framework.start("IEBus loopback test")
        min_bias = self.__framework.args.min_bias
        max_bias = self.__framework.args.max_bias
        bias_step = self.__framework.args.bias_step
        self.__framework.fixtureSetMux(InputMux.NoConnect, OutputMux.NoConnect)
        self.__framework.consoleSend(command="test_ie reset")
        # self.__framework.fixtureSetDacValue(DacChannel.DacChannel1, 0)
        time.sleep(1.0)

        for bias in range(min_bias, max_bias + 1, bias_step):
            self.scanAtVoltage(bias)


if __name__ == "__main__":

    parser = TestArguments("IebusTest")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        test = IebusTest(framework)
        test.run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
