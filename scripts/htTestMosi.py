#! /usr/bin/env python3
import argparse
import time
from analog import *
from framework import *


class HtTestMosi():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework

    def run(self):
        self.__framework.start("HT Mosi loopback")

        # setup mux for
        #       output HT:MC_MOSI_TX       -->
        #       input  HT:IR_MOSI_RX       <--
        self.__framework.fixtureSetMux(InputMux.HtIrMosi, OutputMux.HtMcMosi)
        self.__framework.fixtureSerialReset()
        self.__framework.consoleSend(command="test_ht reset")
        self.__framework.consoleSend(command="test_ht passthrough on")

        self.__framework.pause()
        data_out = HexCodec.encodeDataStr([i for i in range(40)])
        self.__framework.fixtureSerialSendData(data=data_out, wait=False)

        # time.sleep(0.01)
        adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseHtIrMosi, size=120)
        classes = AnalogData.clasifyAnalogData(adcData, [0.5, 10.0])
        self.__framework.addStepNote(f"Driver Voltage Classes: {classes}")

        self.__framework.pause()
        data_in = self.__framework.fixtureSerialRead(40)
        result = self.__framework.consoleSend(command="test_ht read")
        con_in = parseData(result[0])

        # print("data_in", type(data_in), data_in)
        # print("data_out", type(data_out), data_out)
        # print("data_con", type(con_in), con_in)
        self.__framework.addResult(name="HT Passthrough on",
                                   result=(data_out == data_in) and (data_in == con_in))
        self.__framework.addResult(name="HT Mosi Driver Voltages",
                                   result=(classes[0] > 20 and classes[2] > 20))

        self.__framework.consoleSend(command="test_ht reset")
        self.__framework.consoleSend(command="test_ht passthrough off")

        self.__framework.pause()
        data_out = '[80,81,82,83,84,85,86,87,88,89,8a,8b,8c,8d,8e,8f]'
        self.__framework.fixtureSerialSendData(data_out)

        self.__framework.pause()
        data_in = self.__framework.fixtureSerialRead(16, expect_ack=False)
        result = self.__framework.consoleSend(command="test_ht read")
        con_in = parseData(result[0])

        data_out2 = "[30,31,32,33,34,35,36,37,38,39,3a,3b,3c,3d,3e,3f]"
        self.__framework.consoleSend(command=f"test_ht send {data_out2}")

        self.__framework.pause()
        data_in2 = self.__framework.fixtureSerialRead(16, expect_ack=False)

        self.__framework.addResult(name="HT Passthrough off",
                                   result=(data_in == "[]") and (con_in == data_out) and (data_in2 == "[]"))


if __name__ == "__main__":
    parser = TestArguments("HtTestMosi")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        test = HtTestMosi(framework)
        test.run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
