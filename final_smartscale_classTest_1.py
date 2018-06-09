#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ================ Libraries ===============================
import math
import collections
import time
import bluetooth
import sys
import subprocess
import csv
from ISStreamer.Streamer import Streamer
from random import randint
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, ion, show
import matplotlib.animation as animation
import time
import pyaudio
import numpy as np
import threading
from pynput.keyboard import Key, Listener

# ================ Classes ===============================
from scale_classes_1 import EventProcessor
from scale_classes_1 import Wiiboard
from scale_classes_1 import BoardEvent
from scale_classes_1 import BackgroundSoundCont

# ================= User Settings ====================
BUCKET_NAME = ":apple: My Weight History"
BUCKET_KEY = "weight11"
ACCESS_KEY = "PLACE YOUR INITIAL STATE ACCESS KEY HERE"
METRIC_UNITS = False
WEIGHT_SAMPLES = 250
THROWAWAY_SAMPLES = 75
WEIGHT_HISTORY = 7

# ================= WiiBoard Parameters ====================
CONTINUOUS_REPORTING = "04"  # Easier as string with leading zero
COMMAND_LIGHT = 11
COMMAND_REPORTING = 12
COMMAND_REQUEST_STATUS = 15
COMMAND_REGISTER = 16
COMMAND_READ_REGISTER = 17
INPUT_STATUS = 20
INPUT_READ_DATA = 21
EXTENSION_8BYTES = 32
BUTTON_DOWN_MASK = 8
TOP_RIGHT = 0
BOTTOM_RIGHT = 1
TOP_LEFT = 2
BOTTOM_LEFT = 3
BLUETOOTH_NAME = "Nintendo RVL-WBC-01"

def main():
    
    processor = EventProcessor()

    board = Wiiboard(processor)

    if len(sys.argv) == 1:
        print "Discovering board..."
        address = board.discover()
    else:
        address = sys.argv[1]

    try:
        # Disconnect already-connected devices.
        # This is basically Linux black magic just to get the thing to work.
        subprocess.check_output(["bluez-test-input", "disconnect", address], stderr=subprocess.STDOUT)
        subprocess.check_output(["bluez-test-input", "disconnect", address], stderr=subprocess.STDOUT)
    except:
        pass

    print "Trying to connect..."
    board.connect(address)  # The wii board must be in sync mode at this time
    board.wait(200)
    # Flash the LED so we know we can step on.
    board.setLight(False)
    board.wait(500)
    board.setLight(True)

    sound = BackgroundSoundCont()
    sound.start()

    raw_input ("Ready? Start Calibration Testing?")
    board.calibrateWeightTest() # after this measureCounter = 0
    raw_input ("Ready? Start Testing!")
    board.receiveTest()         # after this measureCounter = 0

    raw_input ("Ready? Start Calibration with Two Feet?")
    board.calibrateWeight()       # after this MC = 1
    raw_input ("Start Balancing with Sound Feedback? Close Eyes when Ready")       
    board.receive()               # at start MC = 1, after MC = 2             
    board.check()
    raw_input ("Ready to Balance without Sound? Close Eyes when Ready")
    board.receive()               # at start MC = 2, after MC = 3  
    board.check()    

    raw_input ("Ready? Start Calibration with One Foot?")
    board.calibrateWeight()       # after this MC = 4
    raw_input ("Start Balancing with Sound Feedback? Close Eyes when Ready")       
    board.receive()               # at start MC = 4, after MC = 5                 
    board.check()
    raw_input ("Ready to Balance without Sound? Close Eyes when Ready")
    board.receive()               # at start MC = 5, after MC = 6    
    board.check()
    
    raw_input ("Ready? Start Calibration with One Foot and Support?")
    board.calibrateWeight()       # after this MC = 7    
    raw_input ("Start Balancing with Sound Feedback? Close Eyes when Ready")       
    board.receive()               # after MC = 8  
    board.check()
    raw_input ("Ready to Balance without Sound? Close Eyes when Ready")
    board.receive()               # after MC = 9
    board.check()
    board.disconnect()

if __name__ == "__main__":
    
    file2F_WS = open("2F_WS_1.csv", 'w+')
    file2F_WS.close()
    file2F_OS = open("2F_OS_1.csv", 'w+')
    file2F_OS.close()
    file1FB_WS = open("1FB_WS_1.csv", 'w+')
    file1FB_WS.close()
    file1FB_OS = open("1FB_OS_1.csv", 'w+')
    file1FB_OS.close()
    file1FS_WS = open("1FS_WS_1.csv", 'w+')
    file1FS_WS.close()
    file1FS_OS = open("1FS_OS_1.csv", 'w+')
    file1FS_OS.close()
    totalWeight = csv.writer(open("allWeights_1.csv",'w+'))
    
    main()


