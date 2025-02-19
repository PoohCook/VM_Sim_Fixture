#! /usr/bin/env python3
import argparse
import time
from analog import *
from framework import *
from datetime import datetime



if __name__ == "__main__":
    parser = TestArguments("SB4 Manufacturing Test")
    args = parser.parse_args()
    framework = TestFramework(args=args, spinup=False)

    print(f"power: {args.power_off}")
    if args.power_off:
        framework.powerSetup(on=False)
    else:
        framework.powerSetup(on=True)

    framework.shutdown()
