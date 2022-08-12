##
## Project: LoRa Toolbox
## File name:: main.py
## Created by: Manuel Bechel (SES) for Trier University of Applied Sciences
## Date: 12.08.2022
##
## Description: The LoRa Toolbox provides a simple start to play around with
## LoRa enbaled PyCom LoPy 4 Microcontrollers. Targeted audience for this project
## are students, teachers and other interested persons with no or only basic 
## knowledge in radio frequency based transmissions and reception or even 
## coding at all. The more advanced audience can adapt, improve or extend this code.
## 
##

# Libraries
from network import WLAN
from network import LoRa
import machine
import socket
import time
import pycom

print("main.py - V1.8")

# constants
BW125 = LoRa.BW_125KHZ
BW250 = LoRa.BW_250KHZ
BW500 = LoRa.BW_500KHZ
FEC45 = LoRa.CODING_4_5
FEC46 = LoRa.CODING_4_6
FEC47 = LoRa.CODING_4_7
FEC48 = LoRa.CODING_4_8
PORT = 4711
WIFI = False
SSID = 'LoRaToolbox'
PW = '1234567890'
IP = '0.0.0.0'

#variables initialization as method (to re-run after Tx and Rx) / fallback valuess
def initVARS():
    Mode = "none"
    SF = 12
    FQ = 868000000
    BW = 125
    TX = 12
    FEC = 4_5
    MSG =  "LoRa"
    FECparam = LoRa.CODING_4_5
    BWparam = LoRa.BW_125KHZ
    Repeat = 10
    Pause = 2
    lora_list = []

# first init of the variables
initVARS()

# WiFi setup
wlan = WLAN(mode = WLAN.STA) # create station interface
nets = wlan.scan()

# As there are several bugs existing and the access point connection is not that reliable
# on the Pycom MicroPython release, the whole connection and establishing process has to be
# supported with additional functions, loops and conditions. Only with this complicated 
# code for such simple tasks is an almost reliable WIFI connection possible.

def connectWIFI():
    global WIFI
    global SSID
    global PW
    for net in nets:
        if net.ssid == SSID: 
            wlan.connect(net.ssid, auth=(net.sec, PW), timeout=5000) 
            for _ in range (20):
                if wlan.isconnected():
                    break
                else:
                    print("Trying to connect to WIFI - Attempt number {}".format(_+1))
                    wlan.connect(net.ssid, auth=(net.sec, PW), timeout=5000)
                    time.sleep(1)
            print('WLAN connection succeeded!')
            WIFI=True
            break

while WIFI == False:
    time.sleep(1)
    connectWIFI()


IP = wlan.ifconfig()[0]
print("LoPy has the IP: {}".format(IP))
# disabling the blue heartbeat LED
pycom.heartbeat(False)

# Mainloop Socket init 
ipSocket = socket.socket()
ipSocket.bind(('', PORT))
print("socket binded to %s" % (PORT))
ipSocket.listen(5)
print("socket is listening")

# function to send a socket over the network to a given IP address
# as the LoRa Tx, Rx or even scan sessions might be a bit longer
# it's possible that a socket is already closed and the reply to 
# the already open Mainloop socket will fail. 
# Therefore the mainloop socket is closed on the client site after
# transmission as the client has an always open listener socket
def sendSocket(addr, mode, status, freq, sf):
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((addr, PORT))   
        clientSocket.sendall("{}:{}:{}:{}:{}\n".format(IP, mode, status, freq, sf)) 
        clientSocket.close()
    except socket.error:
        print('Socket Error')
    except:
        print('Problem during Socket connection')
    

# function for the LoRa Rx
def LoRaRX(addr, msg):
    # Counter and time variables
    i = 1
    epochTime = int(time.time())
    durationTime = int(float(Repeat))*60
    # LoRa Rx settings
    lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, sf=int(SF), frequency=int(FQ))
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s.setblocking(False)
    if int(float(Repeat)) == 0:
        print("Receive Loop started, MicroController needs a reset to receive new inputs")
        sendSocket(addr, 'RX','START', 0, 0)
        while True:
            #if s.recv(64) == b'LoRa Toolbox':
            if s.recv(64) == msg.encode('utf-8'):
                print('LoRa message received - Nr. {}'.format(i))
                sendSocket(addr, 'RX','SUCCESS', FQ, SF)
                i = i+1
            time.sleep(0.1)
    else:
        print("Repeat for {} minutes".format(int(float(Repeat))))
        sendSocket(addr, 'RX','START', 0, 0)
        while int(time.time()) < epochTime+durationTime:
            if s.recv(64) == msg.encode('utf-8'):
                print('Msg received - Nr. {}'.format(i))
                sendSocket(addr, 'RX','SUCCESS', FQ, SF)
                i = i+1
            time.sleep(0.1)
        sendSocket(addr, 'RX','END', 0, 0)
    s.close()

# function for the scanning mode
def scan(addr, msg):
    print("Scan Loop started, MicroController needs a reset to receive new inputs")
    sendSocket(addr, 'SCAN','START', 0, 0)
    for freq in range(863000000, 880000000, 1000000):
        print("Freq {}".format(freq))
        for sf in range(7, 13, 1):
            print("SF {}".format(sf))
            lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, sf=int(sf), frequency=int(freq))
            s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
            s.setblocking(False)
            s.settimeout(10.0)
            epochTime = int(time.time())
            try:
                if s.recv(64):
                    print('LoRa message received on frequency {} with SF {}'.format(freq, sf))
                    sendSocket(addr, 'SCAN','SUCCESS', freq, sf)
            except socket.timeout:
                print('No packet received on this freq+sf')
    sendSocket(addr, 'SCAN','END', 0, 0)       
    s.close()


# function for the LoRa Tx
def LoRaTX(addr, msg):
    # adjusting the LoRa parameters to match the required format
    if BW == 125:
        BWparam = BW125
    elif BW == 250:
        BWparam = BW250
    elif BW == 500:
        BWparam = BW500
    else:
        BWparam = BW125
    if FEC == 4_6:
        FECparam = FEC46
    elif FEC == 4_7:
        FECparam = FEC47
    elif FEC == 4_8:
        FECparam = FEC48
    else:
        FECparam = FEC45

    # LoRa Tx settings
    lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868, frequency=int(FQ), bandwidth=BWparam, coding_rate=FECparam, sf=int(SF), tx_power=int(TX))
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    if int(float(Repeat)) == 0:
        print("while True loop started with {} seconds of pause between the transmits".format(int(float(Pause))))
        print("A reset is required to start receive different instructions")
        sendSocket(addr, 'TX','START', 0, 0)       
        while True:
            s.setblocking(True)
            s.send(msg)
            pycom.heartbeat(True)
            time.sleep(int(float(Pause)))
    else:
        print("Tx for loop started with {} iterations and {} seconds of pause in between".format(int(float(Repeat)), int(float(Pause))))
        sendSocket(addr, 'TX','START', 0, 0)       
        for x in range(int(float(Repeat))):
            s.setblocking(True)
            s.send(msg)
            pycom.heartbeat(True)
            time.sleep(int(float(Pause)))
        print("Transmit finished")
        sendSocket(addr, 'TX','END', 0, 0)       
        pycom.heartbeat(False)
    s.close()


# Main loop for the MicroController
while True:
    print('Ready for new connection')
    c, addr = ipSocket.accept()
    print('Got connection from', addr)
    data = c.recv(1024).decode()
    # Splitting surrounded by a try/except in case a random socket or incorrect instruction set is received
    try:
        lora_list = data.split(":")
        print("Received following instructions:")
        # Example for valid instructions TX:11:125:868000000:13:20:1:4_5:LoRa:
        # That instruction will be split and each value will be assigned to the program's variables
        print(lora_list)
        Mode = lora_list[0]
        SF = lora_list[1]
        BW = lora_list[2]
        FQ = lora_list[3]
        TX = lora_list[4]
        FEC = lora_list[7]
        Repeat = lora_list[5]
        Pause = lora_list[6]
        Msg = lora_list[8]
        if Mode == "TX":
            print("Starting Tx")
            LoRaTX(addr[0], Msg)
        if Mode == "RX":
            print("Starting Rx")
            LoRaRX(addr[0], Msg)
        if Mode == "SCAN":
            print("Starting Scan mode")
            scan(addr[0], Msg)
        initVARS()
    except:
        print("Error! Please check the parameters and the network. Also a 'rogue socket connection' could be the case")
    c.close()
    time.sleep(0.01)
