#!/usr/bin/env python3

# Program: An IOT client implementation for University of Nevada, Reno CPE 401
# Filename: IOT Client.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_DGRAM
import argparse as ap
import hashlib
import sys
from time import time

# Use Command Line arguments to get pertinent information
parser = ap.ArgumentParser()
parser.add_argument("-d", "--device", required=True, help="The name of the device")
parser.add_argument("-s", "--server", required=True, help="The IP of the server")
parser.add_argument("-p", "--port", required=True, help="The port that the server is on")
parser.add_argument("-dp", "--device_port", required=True, help="The device listening port")

args = vars(parser.parse_args())

# Menu options for the user to select
menu = {"1": "Register Device", "2": "Deregister Device",
        "3": "Login", "4": "Logoff", "0": "Quit"}


# A Data Structure that holds all relevant functions pertaining to the
class IOTclient:
    s = socket(AF_INET, SOCK_DGRAM)
    # Class Variables
    server = ()
    deviceID = ''
    passPhrase = ''
    MAC = ''
    IP = ''
    serverPort = ''
    port = 0

    # Constructor for the Object
    def __init__(self, d, pp, m, i, p, s, dp):
        self.deviceID = d
        self.passPhrase = pp
        self.MAC = m
        self.IP = i
        self.serverPort = p
        self.server = s, p
        self.port = int(dp)

    # This binds the client to the listening port
    def bindClient(self):
        self.s.bind(('127.0.0.1', self.port))

    # Send the register message to the server
    def register(self):
        reg = ("REGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC + "\t" + self.IP + "\t"
               + str(self.port))
        reg = reg.encode('ascii')
        self.s.sendto(reg, self.server)
        self.processMessage()

    # Send the deregister message to the server
    def deregister(self):
        dereg = ("DEREGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC + "\t" + self.IP + "\t"
                 + str(self.port))
        dereg = dereg.encode('ascii')
        self.s.sendto(dereg, self.server)
        self.processMessage()

    # Send the login message to the server
    def login(self):
        login = ("LOGIN\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.IP + "\t" + str(self.port))
        login = login.encode('ascii')
        self.s.sendto(login, self.server)
        self.processMessage()

    # Send the logoff message to the server
    def logoff(self):
        logoff = ("LOGOFF\t" + self.deviceID)
        logoff = logoff.encode('ascii')
        self.s.sendto(logoff, self.server)
        self.processMessage()

    # Send data that is requested by the server
    def sendData(self, dcode, length, data):

        timeStamp = int(time())
        reply = ("DATA\t" + dcode + '\t' + self.deviceID + '\t' + str(timeStamp) + '\t' + length + '\t' + data)
        reply = reply.encode('ascii')
        self.s.sendto(reply, self.server)

    # This function processes the query message and will be fully implemented when more is known
    def processQuery(self, msg):
        if msg[1] == '':
            dcode = 0
            data = "Sensor Data"
            length = data.count(data)
            self.sendData(dcode, length, data)

    # This is a function to process the ACK message that comes from the server
    def processACK(self, msg):
        if msg[1] == '00':
            print("Device " + msg[2] + " Registered")
        elif msg[1] == '01':
            print("Device " + msg[2] + " Previously Registered")
        elif msg[1] == '02':
            print(msg[2] + "'s IP Changed")
        elif msg[1] == '12':
            print("IP Already in Use")
        elif msg[1] == '13':
            print("MAC Address Already in use")
        elif msg[1] == '20':
            print("Device " + msg[2] + " Deregistered")
            self.s.close()
            sys.exit(1)
        elif msg[1] == '21':
            print("Device did not exist")
            self.s.close()
        elif msg[1] == '30':
            print("Device is already registered with another MAC or IP")
            self.s.close()
        elif msg[1] == '31':
            print("Device is not registered")
        elif msg[1] == '50':
            print("Device Data received")
        elif msg[1] == '51':
            print("Device is not registered")
        elif msg[1] == '70':
            print("Device is logged on")
        elif msg[1] == '80':
            print("Device id logged off")
            self.s.close()
            sys.exit(1)

    # Once a message is sent, this waits for a reply
    def processMessage(self):
        data, addr = self.s.recvfrom(1024)
        msg = data.decode('ascii')
        newMsg = msg.split('\t')
        if newMsg[0] == "QUERY":
            self.processQuery(newMsg)
        elif newMsg[0] == "ACK":
            self.processACK(newMsg)

        # print("received", newMsg, "from", addr)


# The main menu for the program
def mainMenu(device):
    while True:
        options = menu.keys()
        print("Choose a function to perform:")
        for entry in options:
            print(entry, menu[entry])
        selection = input("Select an action:")
        if selection == '1':
            device.register()
        elif selection == '2':
            device.deregister()
        elif selection == '3':
            device.login()
        elif selection == '4':
            device.logoff()
        elif selection == '0':
            break


# Main function to run the program
def main():
    # Initialize the device with values
    device = IOTclient(args["device"], "toor", "BB:CC:DD:EE:FF:GG", "192.168.1.10",
                       int(args["port"]), args["server"], args["device_port"])
    device.bindClient()
    mainMenu(device)


if __name__ == "__main__":
    main()
