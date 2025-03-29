#! /usr/bin/env python3
import argparse
import time
import json
from analog import *
from framework import *
from tenht import codec, HtDataFrame, HtRecord
from htCounter import HtCounter
from threading import Thread
from serial.serialutil import SerialException
from datetime import datetime

class HtSimulator(Thread):
    def __init__(self, framework: TestFramework) -> None:
        super().__init__()

        self.__framework = framework
        self.htConfig = "0d0b00061038899869950d0d0006109158597797f936d1d031"
        self.ht_codec = codec.HtRecordCodec()
        self.ht_codec.set_htConfig(self.htConfig)

    def load_config(self):
        with open("ht_simulator.cfg", "r") as f:
            cfg = json.load(f)

        self.htConfig = cfg["htConfig"]
        self.columns = cfg["columns"]
        self.__counters = []

        for cntr in cfg["counters"]:
            self.__counters.append(HtCounter(cfg=cntr))

    def save_config(self):
        cfg = {
            "htConfig": self.htConfig,
            "columns": self.columns,
            "counters": []
        }

        for c in self.__counters:
            cfg["counters"].append(c.render())

        with open("ht_simulator.cfg", "w") as f:
            json.dump(cfg, f, indent=2)

    def get_counter(self, counter) -> HtCounter:
        for c in self.__counters:
           if c.ht_code == counter:
                return c
        return None

    def wait_com_request(self):
        if self.__framework.fixtureSerialSendWaitComRequest():
            self.__framework.fixtureSerialReset()
            self.send_ack()
            return True
        return False

    def send_ack(self):
        data_out = HexCodec.encodeDataStr([17])  # 0x11 Ack
        self.__framework.fixtureSerialSendData(data=data_out, wait=True)

    def receive_records(self):
        data_in = self.__framework.fixtureSerialRead(240, expect_ack=False)
        data_in = HexCodec.decodeDataStr(data_in)

        result = self.ht_codec.decodeRecords([HtDataFrame(data_in)])
        self.send_ack()
        return result

    def extract_records(self, code, records):
        for record in records:
            if record.ht_code == code:
                return record.items
        return []

    def encode_hex(self, codes):
        hex_codes = [int(c, 16) for c in codes]
        return hex_codes

    def run(self):
        self.__framework.start("HT Simulator", mute_std=True)
        self.load_config()

        self.setup_mux()

        self.run_request_loop()

    def setup_mux(self):
        # setup mux for
        #       output HT:MC_MOSI_TX       -->
        #       input  HT:MC_MISO_RX       <--
        self.__framework.fixtureSetMux(InputMux.HtMcMiso, OutputMux.HtMcMosi)
        self.__framework.fixtureSerialReset()

        # self.save_config()

    def run_request_loop(self):
        while True:
            try:
                if self.wait_com_request():
                    self.process_request()
            except KeyboardInterrupt:
                break
            except SerialException:
                break
            except Exception as e:
                self.log(f"Req Error: {e}, {type(e)}")
                pass

    def log(self, msg):
        with open("ht_simulator.log", "a") as f:
            msg_with_timestamp = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} {msg}\n"
            f.write(msg_with_timestamp)

    def process_request(self):
        security_recs = self.receive_records()
        cred1 = self.extract_records(0x0d0b, security_recs)
        cred2 = self.extract_records(0x0d0d, security_recs)
        self.log(F"result cred1: {cred1} cred2: {cred2}")

        command_recs = self.receive_records()

        action = self.extract_records(0x0aa0, command_recs)[0]
        codes = self.extract_records(0x0a1a, command_recs)
        hex_codes = self.encode_hex(codes)
        self.log(f"processing action: {action}, codes: {codes}")

        for code in hex_codes:
            counter = self.get_counter(code)
            items = counter.encode_values()
            self.log(f"counter: {code:04X}, items: {items}")

            out_frame = HtRecord(ht_code=code, item_length=counter.size, items=items)
            out_data = self.ht_codec.encodeRecords([out_frame])

            for data in out_data:
                data_out = HexCodec.encodeDataStr(data.data)
                self.__framework.fixtureSerialSendData(data=data_out, wait=False)

            resp = self.get_response()
            self.log(f"response received: {resp}")

    def get_response(self):
        start_time = time.time()
        while (time.time() - start_time) < 2.0:
            data_in = self.__framework.fixtureSerialRead(20, expect_ack=False)
            if len(data_in) > 2:
                return data_in

        return "[]"

    def process_ui_command(self, command):
        match = re.match(r"(\w+)\s+(\w+)\[(\d+)\](?:=(\d+))?", command)

        if match:
            result = list(match.groups())
            # ['set', '0BC4', '8', '123']
            action = result[0]
            counter = int(result[1],16)
            index = int(result[2])
            value = int(result[3]) if result[3] else None
            if action.lower() == "set":
                self.set_counter_value(counter, index, value)
                return

            if action.lower() == "inc":
                self.inc_counter_value(counter, index)
                return

            if action.lower() == "get":
                self.get_counter_value(counter, index)
                return

            else:
                print(f"action {action} not recognized")

        else:
            print("command not recognized")

    def set_counter_value(self, counter, index, value):
        counter = self.get_counter(counter)
        if counter is None:
            print(f"counter {counter} not found")
            return

        if index >= counter.size:
            print(f"index {index} out of range")
            return

        if value is None:
            print("value not specified")
            return

        counter.set_value(index, value)
        self.save_config()

    def inc_counter_value(self, counter, index):
        counter = self.get_counter(counter)
        if counter is None:
            print(f"counter {counter} not found")
            return

        if index >= counter.size:
            print(f"index {index} out of range")
            return

        counter.inc_value(index)
        self.save_config()

    def get_counter_value(self, counter, index):
        counter = self.get_counter(counter)
        if counter is None:
            print(f"counter {counter} not found")
            return
        if index >= counter.size:
            print(f"index {index} out of range")
            return
        value = counter.get_value(index)
        print(f"{counter.ht_code:04X}[{index}]={value}")

    def run_ui(self):
        while True:
            try:
                response = input("SIM: ")
                self.process_ui_command(response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error: {e}")
                pass

        try:
            self.__framework.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    parser = TestArguments("HtTestMosi")
    args = parser.parse_args()
    framework = TestFramework(args=args, spinup=False)

    test = HtSimulator(framework)
    test.start()
    time.sleep(0.5)
    test.run_ui()
