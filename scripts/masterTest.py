#! /usr/bin/env python3
import argparse
import time
from analog import *
from framework import *
from datetime import datetime

from vtsTestSync import VtsTestSync
from vtsTestMosi import VtsTestMosi
from vtsTestMiso import VtsTestMiso
from iebusTest import IebusTest
from htTestMiso import HtTestMiso
from htTestMosi import HtTestMosi
from ledTest import LedTest


if __name__ == "__main__":
    parser = TestArguments("SB4 Manufacturing Test")
    args = parser.parse_args()
    framework = TestFramework(args=args)

    def tests():
        VtsTestMosi(framework).run()
        VtsTestMiso(framework).run()
        VtsTestSync(framework).run()
        IebusTest(framework).run()
        HtTestMiso(framework).run()
        HtTestMosi(framework).run()
        LedTest(framework).run()

    framework.run(tests)

    framework.report()
    framework.shutdown()
