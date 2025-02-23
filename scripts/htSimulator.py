#! /usr/bin/env python3
import argparse
import time
from analog import *
from framework import *
from tenht import codec, HtDataFrame, HtRecord


class HtSimulator():
    def __init__(self, framework: TestFramework) -> None:
        self.__framework = framework
        self.htConfig = "0d0b00061038899869950d0d0006109158597797f936d1d031"
        self.ht_codec = codec.HtRecordCodec()
        self.ht_codec.set_htConfig(self.htConfig)

    def run(self):
        self.__framework.start("HT Mosi loopback")

        # setup mux for
        #       output HT:MC_MOSI_TX       -->
        #       input  HT:IR_MOSI_RX       <--
        self.__framework.fixtureSetMux(InputMux.HtMcMiso, OutputMux.HtMcMosi)
        self.__framework.fixtureSerialReset()
        # self.__framework.consoleSend(command="test_ht reset")
        # self.__framework.consoleSend(command="test_ht passthrough on")

        # self.__framework.pause()
        # data_out = HexCodec.encodeDataStr([17])
        # self.__framework.fixtureSerialSendData(data=data_out, wait=True)
        # for i in range(10):
        #     self.__framework.fixtureSerialSendWaitComRequest()
        #     self.__framework.fixtureSerialSendComRequest()
        #     self.__framework.fixtureSerialReset()
        #     self.__framework.fixtureSerialSendData(data=data_out, wait=True)
        #     self.__framework.fixtureSerialRead(10)

        #     time.sleep(0.5)

        if self.__framework.fixtureSerialSendWaitComRequest():
            self.__framework.fixtureSerialReset()
            data_out = HexCodec.encodeDataStr([17])  # 0x11 Ack
            self.__framework.fixtureSerialSendData(data=data_out, wait=True)

        data_in = self.__framework.fixtureSerialRead(240, expect_ack=False)
        data_in = HexCodec.decodeDataStr(data_in)

        result = self.ht_codec.decodeRecords([HtDataFrame(data_in)])
        print(F"result set 1: {result}")

        data_out = HexCodec.encodeDataStr([17])  # 0x11 Ack
        self.__framework.fixtureSerialSendData(data=data_out, wait=True)

        data_in = self.__framework.fixtureSerialRead(240, expect_ack=False)
        data_in = HexCodec.decodeDataStr(data_in)

        result = self.ht_codec.decodeRecords([HtDataFrame(data_in)])
        print(F"result set 2: {result}")

        data_out = HexCodec.encodeDataStr([17])  # 0x11 Ack
        self.__framework.fixtureSerialSendData(data=data_out, wait=True)

        action = 'none'
        codes = []

        for record in result:
            if record.ht_code == 0x0aa0:
                action = record.items[0]
            if record.ht_code == 0x0a1a:
                codes = record.items

        code_hex = [int(c, 16) for c in codes]
        print(f"action: {action}, codes: {codes}, hex: {code_hex}")

        read_code = int(codes[0], 16)
        values = [i for i in range(0, 28)]
        items = [f"{c:04X}" for c in values]
        print(f"items: {items}")

        out_frame = HtRecord(ht_code=code_hex[0], item_length=4, items=items)
        print(f"out_frame: {out_frame}")
        out_data = self.ht_codec.encodeRecords([out_frame])
        print(f"out_data: {out_data}")

        for data in out_data:
            data_out = HexCodec.encodeDataStr(data.data)
            self.__framework.fixtureSerialSendData(data=data_out, wait=True)

        data_in = self.__framework.fixtureSerialRead(200, expect_ack=False)
        print(f"read code: {read_code}, data in: {data_in}")

        # time.sleep(0.01)
        # adcData = self.__framework.fixtureAdcReadData(channel=SenseChannel.SenseHtIrMosi, size=120)
        # classes = AnalogData.clasifyAnalogData(adcData, [0.5, 10.0])
        # self.__framework.addStepNote(f"Driver Voltage Classes: {classes}")

        # self.__framework.pause()
        # data_in = self.__framework.fixtureSerialRead(40)
        # result = self.__framework.consoleSend(command="test_ht read")
        # con_in = parseData(result[0])

        # # print("data_in", type(data_in), data_in)
        # # print("data_out", type(data_out), data_out)
        # # print("data_con", type(con_in), con_in)
        # self.__framework.addResult(name="HT Passthrough on",
        #                            result=(data_out == data_in) and (data_in == con_in))
        # self.__framework.addResult(name="HT Mosi Driver Voltages",
        #                            result=(classes[0] > 20 and classes[2] > 20))

        # self.__framework.consoleSend(command="test_ht reset")
        # self.__framework.consoleSend(command="test_ht passthrough off")

        # self.__framework.pause()
        # data_out = '[80,81,82,83,84,85,86,87,88,89,8a,8b,8c,8d,8e,8f]'
        # self.__framework.fixtureSerialSendData(data_out)

        # self.__framework.pause()
        # data_in = self.__framework.fixtureSerialRead(16, expect_ack=False)
        # result = self.__framework.consoleSend(command="test_ht read")
        # con_in = parseData(result[0])

        # data_out2 = "[30,31,32,33,34,35,36,37,38,39,3a,3b,3c,3d,3e,3f]"
        # self.__framework.consoleSend(command=f"test_ht send {data_out2}")

        # self.__framework.pause()
        # data_in2 = self.__framework.fixtureSerialRead(16, expect_ack=False)

        # self.__framework.addResult(name="HT Passthrough off",
        #                            result=(data_in == "[]") and (con_in == data_out) and (data_in2 == "[]"))


if __name__ == "__main__":
    parser = TestArguments("HtTestMosi")
    args = parser.parse_args()
    framework = TestFramework(args=args, spinup=False)

    def tests():
        test = HtSimulator(framework)
        test.run()

    framework.run(tests)

    # framework.report()
    framework.shutdown()
