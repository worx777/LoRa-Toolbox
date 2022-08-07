##
## Project: LoRa Toolbox
## File name:: main.py
## Created by: Manuel Bechel (SES) for Trier University of Applied Sciences
## Date: 06.08.2022
##
## Description: The LoRa Toolbox provides a simple start to play around with
## LoRa enbaled PyCom LoPy 4 Microcontrollers. Targeted audience for this project
## are students, teachers and other interested persons with no or only basic
## knowledge in radio frequency based transmissions and reception or even
## coding at all. The more advanced audience can adapt, improve or extend this code.
##
##

# Imports
# required for Regex
import re
# Tkinter GUI imports
import tkinter as tk
import tkinter
from tkinter import ttk, Label, Entry, StringVar, Scale, HORIZONTAL, Button
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
# Threading
from threading import Thread
import threading
from _thread import start_new_thread
# Network sockets
import socket
# OS specific
import platform
import sys
# Time
from datetime import datetime

# constant declaration
BW = ["125", "250", "500"]
FREQ = ["863000000", "864000000", "865000000", "866000000", "867000000", "868000000", "869000000", "870000000"]
FEC = ["4_5", "4_6", "4_7", "4_8"]
SF = ["7", "8", "9", "10", "11", "12"]
TXP = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
IP = socket.gethostname()
PORT = 4711
OS = platform.system()  # OS detection to set proper colors according to system

# Variables
Dark = False
FG_Color = "Black"
BG_Color = "White"

# Debugging infos on application start
print("#DEBUGGING START#")
print("OS: {}".format(OS))
print("IP: {}.".format(IP))

# OS dependent dark mode detection, currently only for macOS and Windows. For Linux the light mode will be used as
# default
if OS == "Darwin":
    import subprocess

    # check the set macOS theme
    def check_theme_darwin():
        try:
            cmd = 'defaults read -g AppleInterfaceStyle'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            return bool(p.communicate()[0])
        except OSError:
            return False
    if check_theme_darwin():
        Dark = True

if OS == "Windows":
    # check the set Windows theme
    def check_theme_windows():
        try:
            import winreg
        except ImportError:
            return False
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        try:
            reg_key = winreg.OpenKey(registry, reg_keypath)
        except FileNotFoundError:
            return False
        for n in range(1024):
            try:
                value_name, value, _ = winreg.EnumValue(reg_key, n)
                if value_name == 'AppsUseLightTheme':
                    return value == 0
            except OSError:
                break
        return False
    if check_theme_windows() == 0:
        Dark = True

# if any of these systems is in dark mode, set the background colors accordingly. 
# macOS can make use of the color 'SystemTransparent' to have it aligned with the systems colors
if Dark:
    FG_Color = "White"
    print("Dark Mode enabled")
    if OS == 'Darwin':
        BG_Color = 'SystemTransparent'
    else:
        BG_Color = 'grey'
else:
    print("Light Mode / Default")

print("BG Color {}".format(BG_Color))
print("FG/Font Color {}".format(FG_Color))
print("#DEBUGGING END#")


# main class for this GUI application
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.comboGqrxFQ = None
        self.textBoxHelp = None
        self.sliderRxDuration = None
        self.sliderRxCycles = None
        self.sliderTxCycles = None
        self.comboRxSF = None
        self.comboRxFEC = None
        self.textBoxTxIP = None
        self.textBoxTxMSG = None
        self.textBoxRxIP = None
        self.sliderTxPause = None
        self.textBoxLog = None
        self.textBoxRxMSG = None
        self.comboRxBW = None
        self.comboRxFQ = None
        self.comboTxTXP = None
        self.comboTxFEC = None
        self.comboTxBW = None
        self.comboTxSF = None
        self.comboTxFQ = None
        # Application window resolution
        self.geometry('500x400')
        # Background color
        self.configure(background=BG_Color)
        # Title bar naming
        self.title('LoRa Toolbox')
        # Tab setup
        self.tabController = ttk.Notebook(self)
        self.tabTx = ttk.Frame(self.tabController)
        self.tabRx = ttk.Frame(self.tabController)
        self.tabHelp = ttk.Frame(self.tabController)
        self.tabLog = ttk.Frame(self.tabController)
        self.tabTools = ttk.Frame(self.tabController)
        self.tabController.add(self.tabTx, text='Tx')
        self.tabController.add(self.tabRx, text='Rx')
        self.tabController.add(self.tabHelp, text='Help')
        self.tabController.add(self.tabLog, text='Log')
        # self.tabController.add(self.tabTools, text='Tools') # to be deactivated after taking screenshots
        # Add Tools tab if OS is LInux
        if OS == "Linux":
            self.tabController.add(self.tabTools, text='Tools')
        self.tabController.pack(expand=1, fill='both')
        design = ttk.Style()
        design.theme_use('default')
        design.configure("TNotebook", background=BG_Color, borderwidth=1)
        design.configure("TNotebook.Tab", background='grey', borderwidth=1)
        design.configure("TFrame", background=BG_Color, borderwidth=1)
        design.map("TNotebook", background=[("selected", 'grey')])
        # Create the GUI elements
        self.create_labels_Tx()
        self.create_labels_Rx()
        self.create_comboboxes_Tx()
        self.create_comboboxes_Rx()
        self.create_textboxes_Tx()
        self.create_textboxes_Rx()
        self.create_textboxes_Log()
        self.create_textboxes_Help()
        self.create_sliders_Tx()
        self.create_sliders_Rx()
        self.create_buttons_Tx()
        self.create_buttons_Rx()
        # self.create_tools_tab() #to be deactivated after taking screenshots
        # If Linux, create the content for the Tools tab
        if OS == "Linux":
            self.create_tools_tab()
        # Start the background listener
        self.handle_listener()
        # Write the first log entry in case everything started normally
        self.logEntry('Application started')

    # function to write a log entry
    def logEntry(self, text):
        self.textBoxLog.configure(state='normal')
        self.textBoxLog.insert(tkinter.INSERT, datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
        self.textBoxLog.insert(tkinter.INSERT, ' - ')
        self.textBoxLog.insert(tkinter.INSERT, text)
        self.textBoxLog.insert(tkinter.INSERT, "\n")
        self.textBoxLog.insert(tkinter.INSERT, "-------------------------------------")
        self.textBoxLog.insert(tkinter.INSERT, "\n")
        self.textBoxLog.configure(state='disabled')

    # function for new outbound socket connection
    def startService(self, host, port, message):
        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect((host, port))
            clientSocket.send(message.encode())
            clientSocket.close()
        except TimeoutError:
            print('Target not found, Timeout.')
        except OSError:
            print("Network is unreachable")
            self.logEntry("ERROR: Network is unreachable for node {}".format(host))

    # function to return the Tx infos in a formatted way + log entry
    def getTxString(self):
        data = ("TX:" + str(self.comboTxSF.get()) + ":" + str(self.comboTxBW.get()) + ":" + str(
            self.comboTxFQ.get()) + ":"
                + str(self.comboTxTXP.get()) + ":" + str(self.sliderTxCycles.get()) + ":" + str(
                    self.sliderTxPause.get()) + ":"
                + str(self.comboTxFEC.get()) + ":" + str(self.textBoxTxMSG.get()) + ":")
        self.logEntry(
            'Tx on IP {} with Msg: {} - {} MHz, SF {}, {} kHz BW, {} FEC, {} watt, {} cycles and {} seconds pause'
                .format(str(self.textBoxTxIP.get()), str(self.textBoxTxMSG.get()),
                        str(self.comboTxFQ.get())[0:3],
                        str(self.comboTxSF.get()),
                        str(self.comboTxBW.get()), str(self.comboTxFEC.get()), str(self.comboTxTXP.get()),
                        str(self.sliderTxCycles.get()),
                        str(self.sliderTxPause.get())))
        # uncomment following line for debugging
        print(data)
        return data

    # function to return the Rx infos in a formatted way + log entry
    def getRxString(self, mode):
        data = (str(mode) + ":" + str(self.comboRxSF.get()) + ":noBW:" + str(self.comboRxFQ.get()) + ":noPower:" +
                str(self.sliderRxDuration.get()) + ":noCycles:noFEC:" + str(self.textBoxRxMSG.get()) + ":")
        self.logEntry('{} on IP {} with Msg: {} - {} MHz, SF {} for {} minutes (0 minutes = infinite)'
                      .format(mode, str(self.textBoxRxIP.get()), str(self.textBoxRxMSG.get()),
                              str(self.comboRxFQ.get())[0:3],
                              str(self.comboRxSF.get()),
                              str(self.sliderRxDuration.get())))
        # uncomment following line for debugging
        print(data)
        return data

    # Function for the Tx Button which starts a new thread with the startService function
    def btnTxFunction(self):
        print('Button Tx clicked')
        thread = threading.Thread(target=self.startService, args=(self.textBoxTxIP.get(), PORT, self.getTxString()))
        try:
            thread.start()
        except OSError:
            print('OSError')

    # Function for the Rx Button which starts a new thread with the startService function
    def btnRxFunction(self):
        print('Button Rx clicked')
        thread = threading.Thread(target=self.startService, args=(self.textBoxRxIP.get(), PORT, self.getRxString('RX')))
        try:
            thread.start()
        except OSError:
            print('OSError')

    # Function for the Scan Button which starts a new thread with the startService function
    def btnRxScanFunction(self):
        print('Button Scan clicked')
        thread = threading.Thread(target=self.startService,
                                  args=(self.textBoxRxIP.get(), PORT, self.getRxString('SCAN')))
        try:
            thread.start()
        except OSError:
            print('OSError')

    # Button functions for setting Gqrx parameters
    def btnGqrxFunction(self):
        print('Frequency in Gqrx change attempt to {}'.format(self.comboGqrxFQ.get()))
        self.logEntry('Set frequency in Gqrx on localhost to: {}'.format(self.comboGqrxFQ.get()))
        thread = threading.Thread(target=self.startService,
                                  args=('127.0.0.1', 7356, "F {}".format(self.comboGqrxFQ.get())))
        try:
            thread.start()
        except OSError:
            print('OSError')

    # Function to create the labels on the Tx tab
    def create_labels_Tx(self):
        Label(self.tabTx, text='IP address:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=0, column=0, padx='10', pady='10')
        Label(self.tabTx, text='LoRa Message:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=1, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Frequency:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=2, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Spreading Factor:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=3, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Bandwidth:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=4, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Forward Error Correction:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=5, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Transmit Power:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=6, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Pause Time:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=7, column=0, padx='10', pady='5')
        Label(self.tabTx, text='Transmit Cycles:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=8, column=0, padx='10', pady='5')

    # function to create a warning label in case of network problems
    def create_label_warning(self):
        Label(self.tabTx, text='Network Error! Please close and restart in a minute', bg=BG_Color, fg='red',
              font=('arial', 12, 'normal')).grid(row=10, column=0)

    # Function to create the labels on the Rx tab
    def create_labels_Rx(self):
        Label(self.tabRx, text='IP address:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=0, column=0, padx='15', pady='10')
        Label(self.tabRx, text='LoRa Message:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=1, column=0, padx='15', pady='5')
        Label(self.tabRx, text='Frequency:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=2, column=0, padx='15', pady='5')
        Label(self.tabRx, text='Spreading Factor:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=3, column=0, padx='15', pady='5')
        Label(self.tabRx, text='Scan duration:', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=4, column=0, padx='15', pady='5')

    # Function to create the comboboxes on the Tx tab
    def create_comboboxes_Tx(self):
        self.comboTxFQ = ttk.Combobox(self.tabTx, values=FREQ, font=('arial', 12, 'normal'), width=24,
                                      background=BG_Color,
                                      state="readonly")
        self.comboTxFQ.grid(row=2, column=1)
        self.comboTxFQ.current(5)

        self.comboTxSF = ttk.Combobox(self.tabTx, values=SF, font=('arial', 12, 'normal'), width=24,
                                      background=BG_Color,
                                      state="readonly")
        self.comboTxSF.set(8)
        self.comboTxSF.grid(row=3, column=1)
        self.comboTxSF.current(4)

        self.comboTxBW = ttk.Combobox(self.tabTx, values=BW, font=('arial', 12, 'normal'), width=24,
                                      background=BG_Color,
                                      state="readonly")
        self.comboTxBW.set(125)
        self.comboTxBW.grid(row=4, column=1)
        self.comboTxBW.current(0)

        self.comboTxFEC = ttk.Combobox(self.tabTx, values=FEC, font=('arial', 12, 'normal'), width=24,
                                       background=BG_Color,
                                       state="readonly")
        self.comboTxFEC.grid(row=5, column=1)
        self.comboTxFEC.current(0)

        self.comboTxTXP = ttk.Combobox(self.tabTx, values=TXP, font=('arial', 12, 'normal'), width=24,
                                       background=BG_Color,
                                       state="readonly")
        self.comboTxTXP.set(14)
        self.comboTxTXP.grid(row=6, column=1)
        self.comboTxTXP.current(11)

    # Function to create the comboboxes on the Rx tab
    def create_comboboxes_Rx(self):
        self.comboRxFQ = ttk.Combobox(self.tabRx, values=FREQ, font=('arial', 12, 'normal'), width=24,
                                      background=BG_Color,
                                      state="readonly")
        self.comboRxFQ.grid(row=2, column=1)
        self.comboRxFQ.current(5)

        self.comboRxSF = ttk.Combobox(self.tabRx, values=SF, font=('arial', 12, 'normal'), width=24,
                                      background=BG_Color,
                                      state="readonly")
        self.comboRxSF.set(8)
        self.comboRxSF.grid(row=3, column=1)
        self.comboRxSF.current(4)

    # Function to create the textboxes on the Tx tab
    def create_textboxes_Tx(self):
        self.textBoxTxIP = Entry(self.tabTx, textvariable=StringVar(self, value='192.168.100.100'), width=20)
        self.textBoxTxIP.grid(row=0, column=1)

        self.textBoxTxMSG = Entry(self.tabTx, textvariable=StringVar(self, value='LoRa'), width=20)
        self.textBoxTxMSG.grid(row=1, column=1)

    # Function to create the textboxes on the Rx tab
    def create_textboxes_Rx(self):
        self.textBoxRxIP = Entry(self.tabRx, textvariable=StringVar(self, value='192.168.100.100'), width=20)
        self.textBoxRxIP.grid(row=0, column=1)

        self.textBoxRxMSG = Entry(self.tabRx, textvariable=StringVar(self, value='LoRa'), width=20)
        self.textBoxRxMSG.grid(row=1, column=1)

    # Function to create the textbox and all the texts on the help tab
    def create_textboxes_Help(self):
        self.textBoxHelp = ScrolledText(self.tabHelp)
        self.textBoxHelp.pack(fill='both', side='left', expand=True)
        self.textBoxHelp.insert(tkinter.INSERT, "FAQ")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "-------------------------------------")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "How are all applications and devices connected?")
        self.textBoxHelp.insert(tkinter.INSERT, "\n \n")
        self.textBoxHelp.insert(tkinter.INSERT, "All devices shall be in the same network. Make sure, that the "
                                                "Pycom Microcontrollers are either set to your WIFI settings or setup "
                                                "a WIFI with the SSID name LORA with the password 123456789")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "-------------------------------------")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "How can I access the Microcontroller?")
        self.textBoxHelp.insert(tkinter.INSERT, "\n \n")
        self.textBoxHelp.insert(tkinter.INSERT, "Either with Visual Studio Code and the Pycom extension or with a "
                                                "suitable serial terminal application. For Linux and macOS you can "
                                                "use the terminal application 'screen'."
                                                "\n\nExample for macOS:\n\n"
                                                "screen /dev/tty.usbserial-D* 115200"
                                                "\n\nAdditional debugging information will be displayed on this "
                                                "terminal. The Baudrate for this connection is always 115200.")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "-------------------------------------")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "What parameters are supported?")
        self.textBoxHelp.insert(tkinter.INSERT, "\n \n")
        self.textBoxHelp.insert(tkinter.INSERT, "The parameters you can choose for the Tx and Rx are the only "
                                                "available for these specific Microcontrollers. \n"
                                                "These LoRa chips support a frequency range from 863 MHz to 870 MHz, "
                                                "but to make it a bit more simple, this app is limited to steps of"
                                                "1 MHz. Feel free to edit this code to allow a broader scope of "
                                                "the available frequencies within.\n \n"
                                                "All other values represent the existing choices with this hardware.\n"
                                                "Duration, Cycles and Pause time and the LoRa message can be changed "
                                                "as these are only controlling the behaviour and the message content "
                                                "itself.")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "-------------------------------------")
        self.textBoxHelp.insert(tkinter.INSERT, "\n")
        self.textBoxHelp.insert(tkinter.INSERT, "I can't receive the message I'm sending, what could be the reason?")
        self.textBoxHelp.insert(tkinter.INSERT, "\n \n")
        self.textBoxHelp.insert(tkinter.INSERT, "Make sure that the transmitting and receiving unit are set to the "
                                                "same message, frequency and spreading factor. Only if these match "
                                                "the Rx controller will receive it. Yet it's only my implementation "
                                                "that the message has to be the same. This way we make sure that you "
                                                "only receive your message and not all the LoRa messages on the same "
                                                "frequency and SF that all the other nearby LoRa ICs are sending.\n"
                                                "For further analyzing you can use a RTL SDR and an application like "
                                                "GQRX to visualize all the LoRa traffic.")
        self.textBoxHelp.configure(state='disabled')

    # Function to create the log textbox
    def create_textboxes_Log(self):
        self.textBoxLog = ScrolledText(self.tabLog, state='disabled')
        self.textBoxLog.pack(fill='both', side='left', expand=True)

    # Function to create the sliders on the Tx tab
    def create_sliders_Tx(self):
        self.sliderTxPause = Scale(self.tabTx, from_=0, to=10, orient=HORIZONTAL)
        self.sliderTxPause.set(1)
        self.sliderTxPause.grid(row=7, column=1, sticky='NSEW')

        self.sliderTxCycles = Scale(self.tabTx, from_=0, to=100, orient=HORIZONTAL)
        self.sliderTxCycles.set(20)
        self.sliderTxCycles.grid(row=8, column=1, sticky='NSEW')

    # Function to create the sliders on the Rx tab
    def create_sliders_Rx(self):
        self.sliderRxDuration = Scale(self.tabRx, from_=0, to=100, orient=HORIZONTAL)
        self.sliderRxDuration.set(20)
        self.sliderRxDuration.grid(row=4, column=1, sticky='NSEW')

    # Function to create the button on the Tx tab
    def create_buttons_Tx(self):
        Button(self.tabTx, text='Start Tx', font=('arial', 12, 'normal'), command=self.btnTxFunction).grid(pady='10')

    # Function to create the buttons on the Rx tab
    def create_buttons_Rx(self):
        Button(self.tabRx, text='Start Rx', font=('arial', 12, 'normal'), command=self.btnRxFunction).grid(pady='10')
        Button(self.tabRx, text='Scan-Mode', font=('arial', 12, 'normal'), command=self.btnRxScanFunction). \
            grid(pady='10')

    # Function to create the content on the tools tab which is only visible with a Linux OS
    def create_tools_tab(self):
        Label(self.tabTools, text='Start Gqrx', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=0, column=0, padx='10', pady='10')
        Label(self.tabTools, text='Set frequency', bg=BG_Color, fg=FG_Color, font=('arial', 12, 'normal')). \
            grid(row=1, column=0, padx='10', pady='5')
        Button(self.tabTools, text='Start', font=('arial', 12, 'normal'), command=self.startGqrx). \
            grid(row=0, column=1, padx='10', pady='5')
        self.comboGqrxFQ = ttk.Combobox(self.tabTools, values=FREQ, font=('arial', 12, 'normal'), width=24,
                                        background=BG_Color,
                                        state="readonly")
        self.comboGqrxFQ.grid(row=1, column=1)
        self.comboGqrxFQ.current(5)
        Button(self.tabTools, text='Submit', font=('arial', 12, 'normal'), command=self.btnGqrxFunction). \
            grid(row=2, column=1, padx='10')

    # function to start a thread for the socket listener
    def handle_listener(self):
        threading.Thread(target=self.ListenerDaemonFunc, name='Daemon', daemon=True).start()

    # function to start the gqrx application with linux
    def startGqrx(self):
        import os
        try:
            os.system("gqrx >/dev/null 2>&1 &")
        except OSError:
            print("Failed to start GQRX")

    # function to receive the client sockets and check the socket's message
    def ListenerDaemonFunc(self):
        print("ListenerDaemonFunc run")
        # function for each Thread to accept incoming data
        def multiSession(connection):
            connection.send(str.encode('Server is listening'))
            while True:
                data = connection.recv(2048)
                print(data.decode('utf-8'))
                decoded_data = data.decode('utf-8')
                # Regex to check if the message is a specific format. Example: 192.168.100.10:TX:START:868000000:11
                # First part is the IP, second the mode (TX, RX or SCAN), third part the status (START, END or SUCCESS)
                # and the fourth and fifth part is used for successful scans to submit the frequency and spreading
                # factor.
                if re.match('^(?:\d{1,3}\.){3}\d{1,3}:(TX|RX|SCAN):(START|END|SUCCESS):\d{1,10}:\d{1,10}$',
                            decoded_data):
                    splitData = decoded_data.split(":")
                    # If it's a scan success, then the logentry will contain frequency and SF, otherwise not
                    if splitData[2] == 'SUCCESS':
                        self.logEntry("IP: {}, Mode: {}, Status: {}, Freq: {}, Spreading Factor: {}"
                                      .format(splitData[0], splitData[1], splitData[2], splitData[3], splitData[4]))
                    else:
                        self.logEntry("IP: {}, Mode: {}, Status: {}".format(splitData[0], splitData[1], splitData[2]))
                if not data:
                    break
            connection.close()
        # main part of this socket listener which opens a new thread on connection
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
                serverSocket.bind(('', 4711))
                serverSocket.listen()
                ThreadCount = 0
                while True:
                    client, address = serverSocket.accept()
                    # start of new thread on successful socket connection
                    start_new_thread(multiSession, (client,))
                    ThreadCount += 1
                    print('Thread Number: ' + str(ThreadCount))
        except OSError:
            print('OS Error on Server socket')
            self.logEntry('Network problem, please try again')
            serverSocket.close()


# Mainloop of this application which starts the app class and closes the application with all active threads on
# closure of the Tkinter GUI based on the App() class.
if __name__ == "__main__":
    app = App()
    app.mainloop()
    sys.exit()
