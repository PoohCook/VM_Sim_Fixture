# VM_Sim_Fixture

Code for STM32L431 used on VM_Sim_Fixture


Notes on installing for Windows

Install Python 3.11
install Serial Fixture Cable and Serial Console Cable
    figure out what COM ports they are on

py -m pip install -r requirements.txt

execute:
py masterTest.py -c COM_ -f COM_ -pos <serial_num>


example

    py masterTest.py -c COM4 -f COM6 -pos SBE402-M1-230900007



Download STlink tools for windows
