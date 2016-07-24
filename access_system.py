"""access system for Mr. Petrik
python part for raspi
it communicates with alamode shield (arduino)
and django web app
"""

import serial, time
import json
import requests

global codes_json, codes_list

codes_json = []
code_list = []


ser_port = serial.Serial("/dev/ttyS0")
ser_port.baudrate = 115200


def read_command(ser_port): 
    """read command from alamode
    as command is considered line without \r\n"""
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

def download_codes():
    """download codes from web app in json format"""
    global js
    address = "http://vysoky.pythonanywhere.com/access/6eebabbeba3f162859636d349a3e74fd9cbeff5c/dump_codes.json"
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
        if js[i]["card_number"]: 
            list1.append("c" + js[i]["card_number"]
             )
        else: 
            list1.append("k" + js[i]["keyb_number"])
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

def loop():
    global codes_json, codes_list
    last_download = time.time()
    delay_download = 30 * 60
    f = open("logacces.txt", "a", 0)
    f.write("================= restart\n")
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
            print(imsg + str(time.asctime(time.gmtime(time.time()))))
            f.write(imsg + str(time.asctime(time.gmtime(time.time()))) + "\n")
        command = read_command(ser_port)
        if command != "": 
            # command processing
            print("=>" + command)
            if command == "k135797531": 
                # refresh code list
                init() 
                ser_port.write("service\n") 
            elif command[0] in "kc": 
                # validate keyboard or card code
                if command in codes_list: 
                    # open
                    ser_port.write("open\n") 
                    print(codes_json[codes_list.index(command)]["username"])
                else: 
                    # return ko
                    ser_port.write("ko\n")
                    

init()
loop()


