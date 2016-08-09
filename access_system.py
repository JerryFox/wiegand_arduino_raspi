"""access system for Mr. Petrik
python part for raspi
it communicates with alamode shield (arduino)
and django web app
"""

import serial, time
import json
import requests
import datetime 
import os

# download address
ADDRESS = "http://localhost:8000/access/6eebabbeba3f162859636d349a3e74fd9cbeff5c/dump_codes.json"
ADDRESS = "http://vysoky.pythonanywhere.com/access/6eebabbeba3f162859636d349a3e74fd9cbeff5c/dump_codes.json"

global codes_json, codes_list

codes_json = []
codes_list = []


try: 
    ser_port = serial.Serial("/dev/ttyS0")
    ser_port.baudrate = 115200
except: 
    ser_port = False

def read_command(ser_port): 
    """read command from alamode
    as command is considered line without \r\n"""
    if os.path.exists("command.txt"): 
        f = open("command.txt")
        c = list(f)
        f.close()
        if c: 
            c = c[0].split("\n")[0]
        #print(c)
        os.remove("command.txt")
        return c

    if ser_port: 
        command = ""
        delay = 0.2 # how long to wait for a command
        # read until new line 
        begin_time = time.time()
        inchar = ""
        while time.time() < begin_time + delay and inchar != "\n": 
            if ser_port.in_waiting: 
                inchar = ser_port.read()
                command += inchar
        if "\r\n" in command and command.index("\r\n") == len(command) - 2: 
            command = command[:-2]
        return command
    else: 
        return "" 

def download_codes():
    """download codes from web app in json format"""
    global js
    address = ADDRESS
    r = requests.get(address)
    if r.ok: 
        js = r.json()
        json.dump(js, open("dump_codes.json", "w"))
        return js
    else: 
        return False

def create_list(js): 
    list1 = []
    for i in range(len(js)): 
        list1.append(js[i]["code_input"] + js[i]["code_number"])
    return list1


def load_local_json(file="dump_codes.json"): 
    try: 
        js = json.load(open(file))
    except IOError: 
        js = False
    return js

def init(): 
    global codes_json, codes_list
    istate = False
    js = download_codes()
    if not js: 
        js = load_local_json()
        if js:
            codes_json = js
    else: 
        istate = "web"
        codes_json = js
    if not js: 
        print("***** no json data *****")
    else: 
        codes_list = create_list(codes_json)
        if not istate: 
            istate = "local" 
    return istate

def stime(): 
    # ansi date + time with milliseconds
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def loop():
    global codes_json, codes_list
    last_download = time.time()
    delay_download = 30 * 60
    f = open("logacces.txt", "a", 0)
    f.write(stime() + " ====== restart\n")
    while True:
        if time.time() > last_download + delay_download: 
            istate = init()
            last_download = time.time()
            if istate == "web": 
                imsg = "downloaded from web ... "
            elif istate == "local":
                imsg = "refreshed from local ..."
            else: 
                imsg = "download error ... "
            print(stime() + " " + imsg)
            f.write(stime() + " " + imsg + "\n")
        command = read_command(ser_port)
        if command != "": 
            # command processing
            print("=>" + command)
            if command == "k135797531": 
                # refresh code list
                init() 
                ser_port.write("service\n") 
                f.write(stime() + " service" + "\n")
            elif command.startswith("hardOPEN") or command.startswith("softOPEN"): 
                f.write(stime() + " " + command + "\n")
            elif command.startswith("test") or command.startswith("input"): 
                f.write(stime() + " " + command + "\n")
                ser_port.write(command + "\n")
            elif command.startswith("send"): 
                f.write(stime() + " " + command + "\n")
                ser_port.write(command[4:] + "\n")
            elif command[0] in "kc": 
                # validate keyboard or card code
                f.write(stime() + " validate " + command + " - ")
                if command in codes_list: 
                    # open
                    ser_port.write("open\n") 
                    print(codes_json[codes_list.index(command)]["username"])
                    f.write("ok " + codes_json[codes_list.index(command)]["username"]+ "\n")
                else: 
                    # return ko
                    ser_port.write("ko\n")
                    f.write("ko" + "\n")
                    

init()
loop()


