from ctypes import *
import time
maindll = cdll.LoadLibrary("./main4.dll")
id = maindll.detectBoard()
maindll.SetVoltOut.argtypes = [c_int, c_int, c_float]
def setChanVolt(chan, volt):
    maindll.SetVoltOut(0, int(chan), float(volt))

def detectBoard():
    return maindll.detectBoard()



