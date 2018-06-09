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
import pyaudio
import numpy as np
import threading
from pynput.keyboard import Key, Listener

# ================ Global Variables ===============================
playSound = False
pannedLeftVolume = 0.1
pannedRightVolume = 0.1
pitchTopBot = 200
pitchTopBotOld = 200
measureCounter = 0
phase = 0
TT = time.time()

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

class EventProcessor:
    def __init__(self):
        self._measured = False
        self.done = False
        self._measureCnt = 0
        self._events = range(WEIGHT_SAMPLES)
        self._weights = range(WEIGHT_HISTORY)
        self._times = range(WEIGHT_HISTORY)
        self._unit = "lb"
        self._weightCnt = 0
        self._prevWeight = 0
        self._weight = 0
        self._weightChange = 0
        self.streamer = Streamer(bucket_name=BUCKET_NAME,bucket_key=BUCKET_KEY,access_key=ACCESS_KEY)

    def mass(self, event):
        if (event.totalWeight > 2):
            if self._measureCnt < WEIGHT_SAMPLES:
                # if self._measureCnt == 1:
                #     print "Measuring ..."
                #     self.streamer.log("Update", "Measuring ...")
                #     self.streamer.flush()

                if METRIC_UNITS:
                    self._events[self._measureCnt] = event.totalWeight
                    self._unit = "kg"
                else:
                    self._events[self._measureCnt] = event.totalWeight*2.20462
                    self._unit = "lb"
                self._measureCnt += 1                
        else:
            self._measureCnt = 0

    @property
    def weight(self):
        if not self._events:
            return 0
        histogram = collections.Counter(round(num, 1) for num in self._events)
        return histogram.most_common(1)[0][0]

class BoardEvent:   
    
    def __init__(self, topLeft, topRight, bottomLeft, bottomRight, buttonPressed, buttonReleased, 
    topLeftAvg, topRightAvg, bottomLeftAvg, bottomRightAvg):        
        
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft    
        self.bottomRight = bottomRight
        self.buttonPressed = buttonPressed
        self.buttonReleased = buttonReleased
        self.topLeftAvg = topLeftAvg
        self.topRightAvg = topRightAvg
        self.bottomLeftAvg = bottomLeftAvg
        self.bottomRightAvg = bottomRightAvg
        self.totalWeight = topLeft + topRight + bottomLeft + bottomRight  

        self.pannedVolMin = 0.1
        self.pitchMin = 200

        global measureCounter, pannedLeftVolume, pannedRightVolume, pitchTopBot, playSound
        
        
        # if measureCounter == 2 or measureCounter == 3 or measureCounter == 6 or measureCounter == 7 or measureCounter == 10 or measureCounter == 11:
        #     if measureCounter == 2 or measureCounter == 6 or measureCounter == 10:
        #         playSound = True
        #     else:
        #         playSound = False
        #     self.measure()
        # else:
        #     playSound = False

        # if measureCounter == 2 or measureCounter == 6 or measureCounter == 10:
        #     playSound = True
        # else:
        #     playSound = False
        self.measure()

    def measure (self):

        global measureCounter, pannedLeftVolume, pannedRightVolume, pitchTopBot

        topLeftDiff = self.topLeft - self.topLeftAvg
        topRightDiff = self.topRight - self.topRightAvg
        bottomLeftDiff = self.bottomLeft - self.bottomLeftAvg
        bottomRightDiff = self.bottomRight - self.bottomRightAvg
        
        # change fileNum
        if measureCounter == 1:
            with open ("2F_WS_1.csv",'a') as file2F_WS:
                withSoundWriteTwoFeet = csv.writer(file2F_WS)
                withSoundWriteTwoFeet.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        if measureCounter == 2:
            with open ("2F_OS_1.csv",'a') as file2F_OS:
                withoutSoundWriteTwoFeet = csv.writer(file2F_OS)
                withoutSoundWriteTwoFeet.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        if measureCounter == 4:
            with open ("1FB_WS_1.csv",'a') as file1FB_WS:
                withSoundWriteBall = csv.writer(file1FB_WS)
                withSoundWriteBall.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        if measureCounter == 5:
            with open ("1FB_OS_1.csv",'a') as file1FB_OS:
                withoutSoundWriteBall = csv.writer(file1FB_OS)
                withoutSoundWriteBall.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        if measureCounter == 7:
            with open ("1FS_WS_1.csv",'a') as file1FS_WS:
                withSoundWriteSupp = csv.writer(file1FS_WS)
                withSoundWriteSupp.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        if measureCounter == 8:
            with open ("1FS_OS_1.csv",'a') as file1FS_OS:
                withoutSoundWriteSupp = csv.writer(file1FS_OS)
                withoutSoundWriteSupp.writerow([topLeftDiff,topRightDiff,bottomLeftDiff,bottomRightDiff])
        
        sumDiff = abs(topLeftDiff) + abs(topRightDiff) + abs(bottomLeftDiff) + abs(bottomRightDiff)
        
        leftDiff = (self.topLeft + self.bottomLeft) - (self.topLeftAvg + self.bottomLeftAvg) 
        rightDiff = (self.topRight + self.bottomRight) - (self.topRightAvg + self.bottomRightAvg) 

        topBotDiff = abs((topLeftDiff + topRightDiff) - (bottomLeftDiff + bottomRightDiff))

        weightLowerLimit = 1
        weightUpperLimit = 5
        weightDiffRange = weightUpperLimit - weightLowerLimit 
        pitchDiffRange = 20     # to calibrate sensitivity of pitch front and back
        logBase = 6

        if sumDiff < weightLowerLimit:
            pannedLeftVolume = self.pannedVolMin
            pannedRightVolume = self.pannedVolMin
            pitchTopBot = self.pitchMin
        
        else:
            
            if rightDiff >= 0:
                pannedRightVolume = math.log (1 + (rightDiff / weightDiffRange),logBase) + 0.1
            else:
                pannedRightVolume = 0.1

            if leftDiff >= 0:
                pannedLeftVolume = math.log (1 + (leftDiff / weightDiffRange),logBase) + 0.1
            else:
                pannedLeftVolume = 0.1
            
            pitchTopBot = (topBotDiff/pitchDiffRange)*800 + 200
            
            if pitchTopBot >= 1000:
                pitchTopBot = 1000

        print ("TopLeftDiff %.1f TopRightDiff %.1f BottomLeftDiff %.1f BottomRightDiff %.1f" 
        % (topLeftDiff, topRightDiff, bottomLeftDiff, bottomRightDiff))             
        print ("pannedLeftVolume = %.2f" % (pannedLeftVolume))      
        print ("pannedRightVolume = %.2f" % (pannedRightVolume))    
        print ("pitchTopBot = %.2f" % (pitchTopBot))
                                              
class Wiiboard: 
    def __init__(self, processor):
        # Sockets and status
        self.receivesocket = None
        self.controlsocket = None
        self.processor = processor
        self.calibration = []
        self.calibrationRequested = False
        self.LED = False
        self.address = None
        self.buttonDown = False        
        self.topLeftAvg = 0
        self.topRightAvg = 0
        self.bottomLeftAvg = 0
        self.bottomRightAvg = 0
        self.weight = 0
   
        for i in xrange(3):
            self.calibration.append([])
            for j in xrange(4):
                self.calibration[i].append(10000)  # high dummy value so events with it don't register

        self.status = "Disconnected"
        self.lastEvent = BoardEvent(0, 0, 0, 0, False, False, 0, 0, 0, 0)

        try:
            self.receivesocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self.controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        except ValueError:
            raise Exception("Error: Bluetooth not found")

    def isConnected(self):
        return self.status == "Connected"

    # Connect to the Wiiboard at bluetooth address <address>
    def connect(self, address):
        if address is None:
            print "Non existant address"
            return
        self.receivesocket.connect((address, 0x13))
        self.controlsocket.connect((address, 0x11))
        if self.receivesocket and self.controlsocket:
            print "Connected to Wiiboard at address " + address
            self.status = "Connected"
            self.address = address
            self.calibrate()
            useExt = ["00", COMMAND_REGISTER, "04", "A4", "00", "40", "00"]
            self.send(useExt)
            self.setReportingType()
            print "Wiiboard connected"
        else:
            print "Could not connect to Wiiboard at address " + address

    def on_press(self, key):
        print('{0} pressed'.format(
            key))
        if key == Key.esc:
            self.timeout = time.time()
        
    def receive(self):  
        timeout = time.time() + 15
        global measureCounter, playSound         
        # playSound = 1
        # measureCounter += 1

        while self.status == "Connected" and not self.processor.done and timeout > time.time():
            data = self.receivesocket.recv(25)  
            intype = int(data.encode("hex")[2:4])
            print ("Recording data complete in %.0f" % (timeout - time.time()))
            if intype == INPUT_STATUS:
                # TODO: Status input received. It just tells us battery life really
                self.setReportingType()
            elif intype == INPUT_READ_DATA:
                if self.calibrationRequested:
                    packetLength = (int(str(data[4]).encode("hex"), 16) / 16 + 1)
                    self.parseCalibrationResponse(data[7:(7 + packetLength)])
                    if packetLength < 16:
                        self.calibrationRequested = False
            elif intype == EXTENSION_8BYTES:
                self.processor.mass(self.createBoardEvent(data[2:12]))
            else:
                print "ACK to data write received"

        measureCounter += 1
        # playSound = 0
        print ("measureCounter = %f" % (measureCounter))       
            
    def check(self):
        global measureCounter 
        while True:
            answer = str (raw_input ('Run Again? (y/n) :'))
            if answer == 'y':
                measureCounter -= 1

                # change fileNum
                if measureCounter == 1:
                    file2F_WS = open("2F_WS_1.csv", 'w+')
                    file2F_WS.close()
                
                if measureCounter == 2:
                    file2F_OS = open("2F_OS_1.csv", 'w+')
                    file2F_OS.close()
                
                if measureCounter == 4: 
                    file1FB_WS = open("1FB_WS_1.csv", 'w+') 
                    file1FB_WS.close()   
                     
                if measureCounter == 5:
                    file1FB_OS = open("1FB_OS_1.csv", 'w+')
                    file1FB_OS.close()
                    
                if measureCounter == 7:
                    file1FS_WS = open("1FS_WS_1.csv", 'w+')
                    file1FS_WS.close()
                    
                if measureCounter == 8:
                    file1FS_OS = open("1FS_OS_1.csv", 'w+')
                    file1FS_OS.close()
                    
                self.receive()
            else:
                break 

    def receiveTest(self):  
        self.timeout = time.time() + 200
        global playSound, measureCounter    
        # playSound = 1
        measureCounter = 1

        with Listener(
            on_press=self.on_press) as listener:        
            while self.status == "Connected" and not self.processor.done and self.timeout > time.time():
                data = self.receivesocket.recv(25)  
                intype = int(data.encode("hex")[2:4])
                print ("Recording data complete in %.0f" % (self.timeout - time.time()))
                if intype == INPUT_STATUS:
                    # TODO: Status input received. It just tells us battery life really
                    self.setReportingType()
                elif intype == INPUT_READ_DATA:
                    if self.calibrationRequested:
                        packetLength = (int(str(data[4]).encode("hex"), 16) / 16 + 1)
                        self.parseCalibrationResponse(data[7:(7 + packetLength)])
                        if packetLength < 16:
                            self.calibrationRequested = False
                elif intype == EXTENSION_8BYTES:
                    self.processor.mass(self.createBoardEvent(data[2:12]))
                else:
                    print "ACK to data write received"

        measureCounter = 0
        # playSound = 0
        
    def disconnect(self):
        if self.status == "Connected":
            self.status = "Disconnecting"
            # while self.status == "Disconnecting":
            #     self.wait(100)
        try:
            self.receivesocket.close()
        except:
            pass
        try:    
            self.controlsocket.close()
        except:
            pass
        print "WiiBoard disconnected"

    # Try to discover a Wiiboard
    def discover(self):
        print "Press the red sync button on the board now"
        address = None
        bluetoothdevices = bluetooth.discover_devices(duration=6, lookup_names=True)
        for bluetoothdevice in bluetoothdevices:
            if bluetoothdevice[1] == BLUETOOTH_NAME:
                address = bluetoothdevice[0]
                print "Found Wiiboard at address " + address
        if address is None:
            print "No Wiiboards discovered."
        return address
    
    def calibrateWeight(self):
        topLeftrec = []
        topRightrec = []
        bottomLeftrec = []
        bottomRightrec = []
        global measureCounter
        timeout = time.time() + 10   # 5 seconds from now
        
        while self.status == "Connected" and not self.processor.done:
            print "Notice Frequecy and Direction of Noise"
            data = self.receivesocket.recv(25)
            intype = int(data.encode("hex")[2:4])
            if intype == INPUT_STATUS:
                # TODO: Status input received. It just tells us battery life really
                self.setReportingType()
            elif intype == INPUT_READ_DATA:
                if self.calibrationRequested:
                    packetLength = (int(str(data[4]).encode("hex"), 16) / 16 + 1)
                    self.parseCalibrationResponse(data[7:(7 + packetLength)])
                    if packetLength < 16:
                        self.calibrationRequested = False
            elif intype == EXTENSION_8BYTES:
                boardEv = self.createBoardEvent(data[2:12])
                self.processor.mass(boardEv)
                topLeftrec.append(boardEv.topLeft) 
                topRightrec.append(boardEv.topRight) 
                bottomLeftrec.append(boardEv.bottomLeft) 
                bottomRightrec.append(boardEv.bottomRight)  
                # the total i in 5 seconds is 400, the first 100 is usually 0 
                if len(topLeftrec) > 500:       #circular buffer 
                    del topLeftrec[0], topRightrec [0], bottomLeftrec [0], bottomRightrec [0]  
                print ("Top Left = %.2f Top Right = %.2f Bottom Left = %.2f Bottom Right = %.2f" % (boardEv.topLeft, boardEv.topRight, boardEv.bottomLeft, boardEv.bottomRight))
            else:
                print "ACK to data write received"
            
            timeLeft = timeout - time.time()
            print ("Calibration countdown = %.0f ") % (timeLeft)

            if time.time() > timeout:
                self.topLeftAvg = np.mean (topLeftrec)
                self.topRightAvg = np.mean (topRightrec)
                self.bottomLeftAvg = np.mean (bottomLeftrec)
                self.bottomRightAvg = np.mean (bottomRightrec)
                print "Calibration Done"
                print ("Results : Top Left = %.2f Top Right = %.2f Bottom Left = %.2f Bottom Right %.2f" % (self.topLeftAvg, self.topRightAvg, self.bottomLeftAvg, self.bottomRightAvg))
                break

        # change fileNum
        with open ("allWeights_1.csv",'a') as writeWeight:
            totalWeight = csv.writer(writeWeight)                
            totalWeight.writerow([self.topLeftAvg,self.topRightAvg,self.bottomLeftAvg,self.bottomRightAvg])
        
        measureCounter += 1
        print ("measureCounter = %f" % (measureCounter))

    def calibrateWeightTest(self):
        topLeftrec = []
        topRightrec = []
        bottomLeftrec = []
        bottomRightrec = []
        
        timeout = time.time() + 10  

        while self.status == "Connected" and not self.processor.done:
            print "Notice Frequecy and Direction of Noise"
            data = self.receivesocket.recv(25)
            intype = int(data.encode("hex")[2:4])
            if intype == INPUT_STATUS:
                # TODO: Status input received. It just tells us battery life really
                self.setReportingType()
            elif intype == INPUT_READ_DATA:
                if self.calibrationRequested:
                    packetLength = (int(str(data[4]).encode("hex"), 16) / 16 + 1)
                    self.parseCalibrationResponse(data[7:(7 + packetLength)])
                    if packetLength < 16:
                        self.calibrationRequested = False
            elif intype == EXTENSION_8BYTES:
                boardEv = self.createBoardEvent(data[2:12])
                self.processor.mass(boardEv)
                topLeftrec.append(boardEv.topLeft) 
                topRightrec.append(boardEv.topRight) 
                bottomLeftrec.append(boardEv.bottomLeft) 
                bottomRightrec.append(boardEv.bottomRight)  
                # the total i in 5 seconds is 400, the first 100 is usually 0 
                if len(topLeftrec) > 250:       #circular buffer 
                    del topLeftrec[0], topRightrec [0], bottomLeftrec [0], bottomRightrec [0]  
                print ("Top Left = %.2f Top Right = %.2f Bottom Left = %.2f Bottom Right = %.2f" % (boardEv.topLeft, boardEv.topRight, boardEv.bottomLeft, boardEv.bottomRight))
            else:
                print "ACK to data write received"
            
            timeLeft = timeout - time.time()
            print ("Calibration countdown = %.0f ") % (timeLeft)

            if time.time() > timeout:
                self.topLeftAvg = np.mean (topLeftrec)
                self.topRightAvg = np.mean (topRightrec)
                self.bottomLeftAvg = np.mean (bottomLeftrec)
                self.bottomRightAvg = np.mean (bottomRightrec)
                print "Calibration Done"
                print ("Results : Top Left = %.2f Top Right = %.2f Bottom Left = %.2f Bottom Right %.2f" % (self.topLeftAvg, self.topRightAvg, self.bottomLeftAvg, self.bottomRightAvg))
                break       
    
    def createBoardEvent(self, bytes):
        buttonBytes = bytes[0:2]
        bytes = bytes[2:12]
        buttonPressed = False
        buttonReleased = False

        state = (int(buttonBytes[0].encode("hex"), 16) << 8) | int(buttonBytes[1].encode("hex"), 16)
        if state == BUTTON_DOWN_MASK:
            buttonPressed = True
            if not self.buttonDown:
                print "Button pressed"
                self.buttonDown = True

        if not buttonPressed:
            if self.lastEvent.buttonPressed:
                buttonReleased = True
                self.buttonDown = False
                print "Button released"

        rawTR = (int(bytes[0].encode("hex"), 16) << 8) + int(bytes[1].encode("hex"), 16)
        rawBR = (int(bytes[2].encode("hex"), 16) << 8) + int(bytes[3].encode("hex"), 16)
        rawTL = (int(bytes[4].encode("hex"), 16) << 8) + int(bytes[5].encode("hex"), 16)
        rawBL = (int(bytes[6].encode("hex"), 16) << 8) + int(bytes[7].encode("hex"), 16)

        topLeft = self.calcMass(rawTL, TOP_LEFT)
        topRight = self.calcMass(rawTR, TOP_RIGHT)
        bottomLeft = self.calcMass(rawBL, BOTTOM_LEFT)
        bottomRight = self.calcMass(rawBR, BOTTOM_RIGHT)

        topLeftAvg = self.topLeftAvg
        topRightAvg = self.topRightAvg
        bottomLeftAvg = self.bottomLeftAvg
        bottomRightAvg = self.bottomRightAvg

        boardEvent = BoardEvent(topLeft, topRight, bottomLeft, bottomRight, buttonPressed, buttonReleased, topLeftAvg, topRightAvg, bottomLeftAvg, bottomRightAvg)
        return boardEvent

    def calcMass(self, raw, pos):
        val = 0.0
        #calibration[0] is calibration values for 0kg
        #calibration[1] is calibration values for 17kg
        #calibration[2] is calibration values for 34kg
        if raw < self.calibration[0][pos]:
            return val
        elif raw < self.calibration[1][pos]:
            val = 17 * ((raw - self.calibration[0][pos]) / float((self.calibration[1][pos] - self.calibration[0][pos])))
        elif raw > self.calibration[1][pos]:
            val = 17 + 17 * ((raw - self.calibration[1][pos]) / float((self.calibration[2][pos] - self.calibration[1][pos])))

        return val

    def getEvent(self):
        return self.lastEvent

    def getLED(self):
        return self.LED

    def parseCalibrationResponse(self, bytes):
        index = 0
        if len(bytes) == 16:
            for i in xrange(2):
                for j in xrange(4):
                    self.calibration[i][j] = (int(bytes[index].encode("hex"), 16) << 8) + int(bytes[index + 1].encode("hex"), 16)
                    index += 2
        elif len(bytes) < 16:
            for i in xrange(4):
                self.calibration[2][i] = (int(bytes[index].encode("hex"), 16) << 8) + int(bytes[index + 1].encode("hex"), 16)
                index += 2

    # Send <data> to the Wiiboard
    # <data> should be an array of strings, each string representing a single hex byte
    def send(self, data):
        if self.status != "Connected":
            return
        data[0] = "52"

        senddata = ""
        for byte in data:
            byte = str(byte)
            senddata += byte.decode("hex")

        self.controlsocket.send(senddata)

    #Turns the power button LED on if light is True, off if False
    #The board must be connected in order to set the light
    def setLight(self, light):
        if light:
            val = "10"
        else:
            val = "00"

        message = ["00", COMMAND_LIGHT, val]
        self.send(message)
        self.LED = light

    def calibrate(self):
        message = ["00", COMMAND_READ_REGISTER, "04", "A4", "00", "24", "00", "18"]
        self.send(message)
        self.calibrationRequested = True

    def setReportingType(self): 
        bytearr = ["00", COMMAND_REPORTING, CONTINUOUS_REPORTING, EXTENSION_8BYTES]
        self.send(bytearr)

    def wait(self, millis):
        time.sleep(millis / 1000.0)
  

class BackgroundSoundCont (threading.Thread):
    def __init__ (self):
        threading.Thread.__init__(self) 
        self.fs = 44100    # sampling rate, Hz, must be integer
        self.p = pyaudio.PyAudio()
        
    # def callback(self, in_data, frame_count, time_info, status):
    #     global TT, phase, pitchTopBot, pitchTopBotOld, pannedLeftVolume, pannedRightVolume

    #     # changes the phase in addition to the frequency
    #     if pitchTopBot != pitchTopBotOld:
    #         phase = 2*np.pi*TT*(pitchTopBotOld-pitchTopBot)+phase         
    #         pitchTopBotOld = pitchTopBot 
            
    #     sample = (np.sin(phase + 2*np.pi*pitchTopBot*(TT+np.arange(frame_count)/float(self.fs))))
    #     stereo_sample = np.zeros((sample.shape[0]*2,),np.float32)
    #     stereo_sample[1::2] = pannedRightVolume*sample[:]     #1 for right speaker, 0 for  left
    #     stereo_sample[::2] = pannedLeftVolume*sample[:]     #1 for right speaker, 0 for  left            
    #     TT += frame_count/float(self.fs)
    #     return (stereo_sample, pyaudio.paContinue)
    
    # def run (self):

    #     global playSound        # global for disconneting upon esc key
    #     global measureCounter
        
    #     while True:
    #         while playSound:
    #             stream = self.p.open(format=pyaudio.paFloat32,
    #                             channels=2,
    #                             rate=self.fs,
    #                             output=True,
    #                             stream_callback=self.callback)

    #             stream.start_stream()
    #             start = time.time()
    #             try:
    #                 while 1:
    #                     now = time.time()     
    #                     if now-start>1/24.:
    #                         #update the frequency. This will depend on y on the future
    #                         newfreq=200+np.sin(2*np.pi*1/20.*now)*100 
    #                         print newfreq
    #                     start=now
    #             finally:
    #                 stream.stop_stream()
    #                 stream.close()
    #                 self.p.terminate()

    #         if measureCounter == 12:
    #             break
  
    def callback(self, in_data, frame_count, time_info, status):
        global TT, phase, playSound, pitchTopBot, pitchTopBotOld, pannedLeftVolume, pannedRightVolume, measureCounter

        if not measureCounter in [1,4,7]:
            pannedLeftVolume = 0
            pannedRightVolume = 0
            pitchTopBot = 0
        
        # changes the phase in addition to the frequency
        if pitchTopBot != pitchTopBotOld:
            phase = 2*np.pi*TT*(pitchTopBotOld-pitchTopBot)+phase         
            pitchTopBotOld = pitchTopBot 
            
        sample = (np.sin(phase + 2*np.pi*pitchTopBot*(TT+np.arange(frame_count)/float(self.fs))))
        stereo_sample = np.zeros((sample.shape[0]*2,),np.float32)
        stereo_sample[1::2] = pannedRightVolume*sample[:]     #1 for right speaker, 0 for  left
        stereo_sample[::2] = pannedLeftVolume*sample[:]     #1 for right speaker, 0 for  left            
        TT += frame_count/float(self.fs)

        return (stereo_sample, pyaudio.paContinue)


    def run (self):

        global playSound        # global for disconneting upon esc key
        global measureCounter
        
        while 1:        
            stream = self.p.open(format=pyaudio.paFloat32,
                            channels=2,
                            rate=self.fs,
                            output=True,
                            stream_callback=self.callback)
            stream.start_stream()

            try:
                while 1:
                    now = time.time()     
            finally:
                stream.stop_stream()
                stream.close()
                self.p.terminate()

            if measureCounter == 12:
                break
