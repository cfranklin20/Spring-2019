#!/usr/bin/env python3

# Program: An IOT client implementation for University of Nevada, Reno CPE 401
# Filename: IOT Client.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_DGRAM
import argparse as ap

parser = ap.ArgumentParser()
parser.add_argument("-d", "--device", required=True, help="The name of the device")
parser.add_argument("-s", "--server", required=True, help="The IP of the server")
parser.add_argument("-p", "--port", required=True, help="The port that the server is on")

args = vars(parser.parse_args())

menu = {"1": "Register Device", "2": "Deregister Device",
        "3": "Login", "4": "Logoff", "0": "Quit"}


# A Data Structure that holds all relevant functions pertaining to the
class IOTclient:
    s = socket(AF_INET, SOCK_DGRAM)

    server = ()
    deviceID = ''
    passPhrase = ''
    MAC = ''
    IP = ''
    serverPort = ''
    port = 2600

    def __init__(self, d, pp, m, i, p, s):
        self.deviceID = d
        self.passPhrase = pp
        self.MAC = m
        self.IP = i
        self.serverPort = p
        self.server = s, p

    def bindClient(self):
        self.s.bind(('127.0.0.1', self.port))

    # Send the register message to the server
    def register(self):
        reg = ("REGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC + "\t" + self.IP + "\t"
               + str(self.port))
        reg = reg.encode('ascii')
        self.s.sendto(reg, self.server)

    # Send the deregister message to the server
    def deregister(self):
        dereg = ("DEREGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC + "\t" + self.IP + "\t"
                 + str(self.port))
        dereg = dereg.encode('ascii')
        self.s.sendto(dereg, self.server)
        self.s.close()

    # Send the login message to the server
    def login(self):
        login = ("LOGIN\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.IP + "\t" + str(self.port))
        login.encode('ascii')
        self.s.sendto(login, self.server)

    # Send the logoff message to the server
    def logoff(self):
        logoff = ("LOGOFF\t" + self.deviceID)
        logoff.encode('ascii')
        self.s.sendto(logoff, self.server)
        self.s.close()

    # Send data that is requested by the server
    def sendData(self):
        data = ''

    def processData(self):
        data, addr = self.s.recvfrom(1024)
        msg = data.decode('ascii')

        print("received", data, "from", addr)


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


def main():
    device = IOTclient(args["device"], "toor", "AA:BB:CC:DD:EE:FF", "192.168.1.10", int(args["port"]), args["server"])
    device.bindClient()
    mainMenu(device)


if __name__ == "__main__":
    main()
