#! /usr/bin/env python3
import argparse
import time
from analog import *
from framework import *


class VtsTestMiso():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework

    def run(self):
        self.__framework.start("VTS Miso read write")

        # setup mux for
        #       output VTS:MC_MISO_TX_RX       -->
        #       input  VTS:MC_MISO_TX_RX       <--
        self.__framework.fixtureSetMux(InputMux.VtsMcMiso, OutputMux.VtsMcMiso)
        self.__framework.fixtureSerialReset()
        self.__framework.consoleSend(command="test_vts reset")
        self.__framework.consoleSend(command="test_vts passthrough off")

        self.__framework.pause()
        data_out = '[60,61,62,63,64,65,66,67,68,69,6a,6b,6c,6d,6e,6f]'
        self.__framework.fixtureSerialSendData(data_out)

        self.__framework.pause()
        data_in = self.__framework.fixtureSerialRead(16)
        result = self.__framework.consoleSend(command="test_vts read")
        con_in = parseData(result[0])

        # print("data_in", type(data_in), data_in)
        # print("data_out", type(data_out), data_out)
        # print("data_con", type(con_in), con_in)
        self.__framework.addResult(name="Passthrough off",
                                   result=(data_out == data_in) and (data_in == con_in))

        pattern = HexCodec.encodeDataStr([i for i in range(100)])
        self.__framework.fixtureSerialSendData(data=pattern, wait=False)

        time.sleep(0.01)
        adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseVtsMcMiso, size=100)
        classes = AnalogData.clasifyAnalogData(adcData, [0.5, 10.0])

        self.__framework.pause()
        self.__framework.addStepNote(f"Driver Voltage Classes: {classes}")
        self.__framework.addResult(name="MC Miso Driver Voltages",
                                   result=(classes[0] > 20 and classes[2] > 20))


if __name__ == "__main__":
    parser = TestArguments("VtsTestMiso")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        test = VtsTestMiso(framework)
        test.run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
