from ctypes import *
import platform


if platform.system() == 'Darwin':
    def setChanVolt(chan, volt):
        return "Using Mac OS, no S826 board available"

    def detectBoard():
        return "Using Mac OS, no S826 board available"
else:
    maindll = cdll.LoadLibrary("./main4.dll")
    id = maindll.detectBoard()
    maindll.SetVoltOut.argtypes = [c_int, c_int, c_float]


    def setChanVolt(chan, volt):
        maindll.SetVoltOut(0, int(chan), float(volt))


    def detectBoard():
        return maindll.detectBoard()



