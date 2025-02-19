# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and follows
the changelog [Keep a changelog](http://keepachangelog.com/)

## Unreleased
- Sourced user/password for UUT from parameters file (SB-2749)
- Added TestParameters support to enofrce an configure from a document (SB-2749)
- Reconfigured tests so cycling can also include power cycles (SB-2745)
- Added windows packager (SB-2744)
- Added Support for Operator Prompts (SB-2741)
- Added support for cycling uut power (SB-2732)
- Supported command line flashing of Fixture
- Added option to set serial number from command line (SB-2738)
- Added Logout option to all test flows (SB-2728)
- Refactored Console login - connect flow to account for boot time (SB-2728)
- Added Version check to Fixture (SB-2728)
- Provided common TestArgument parser (SB-2736)
- Corrected test pause after 'test_ht passthrough off' for htTestMiso and htTestMosi (SB-2736)
- Corrected test pause after 'test_vts passthrough off' for vtsTestMosi and vtsTestSync (SB-2736)
- Corrected test overrun for vtsTestMiso.py (SB-2736)
- Added run_cycles parameter to each test block (SB-2736)
- Reworked IEbus test to be controllable as to steps taken (SB-2722)
- Added timeout parameter to fixtureAdcReadData (SB-2722)
- Implemented LED Test
- Implemented Ht Test series
- Implemented Master test container
- Implemented VTS test series
- Implemented Iebus Test
- Implemented scripting framework for test construction
- Implemented ADC sense read
- Implemented Test serial read
- Implemented Test serial send
- Implemented Mux control
- Implemented Command protocol
- Initial put
