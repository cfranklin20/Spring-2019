#!/usr/bin/env python3

# Program: An IOT client implementation for University of Nevada, Reno CPE 401
# Filename: IOT Client.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, gethostbyname, gethostname
from threading import Thread, Timer
import argparse as ap
import hashlib
import sys
from time import time
from random import randint

# Use Command Line arguments to get pertinent information
parser = ap.ArgumentParser()
parser.add_argument("-d", "--device", required=True, help="The name of the device")
parser.add_argument("-s", "--server", required=True, help="The IP of the server")
parser.add_argument("-p", "--port", required=True, help="The port that the server is on")

args = vars(parser.parse_args())

# Menu options for the user to select
menu = {"1": "Register Device", "2": "Deregister Device",
        "3": "Login", "4": "Logoff", "5": "Query Client", "0": "Quit"}


# A Data Structure that holds all relevant functions pertaining to the
class IOTclient:
    #TCP Socket
    tcpClient = socket(AF_INET, SOCK_STREAM)
    #UDP Socket
    udpClient = socket(AF_INET, SOCK_DGRAM)
    addr = ''
    # Class Variables
    hostname = gethostname()
    IP = gethostbyname(hostname)

    # Constructor for the Object
    def __init__(self, d, pp, m, p, s):
        self.deviceID = d
        self.passPhrase = pp
        self.MAC = m
        self.serverPort = p
        self.server = s, p

    # This binds the client to the listening port
    def bindClient(self):
        self.tcpClient.bind((self.IP, 0))
        self.udpClient.bind((self.IP, 0))

    # Send the register message to the server
    def register(self):
        reg = ("REGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC)
        reg = reg.encode('ascii')
        self.sendServerMessage(reg)

    # Send the deregister message to the server
    def deregister(self):
        dereg = ("DEREGISTER\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.MAC)
        dereg = dereg.encode('ascii')
        self.sendServerMessage(dereg)

    # Send the login message to the server
    def login(self):
        port = self.udpClient.getsockname()
        login = ("LOGIN\t" + self.deviceID + "\t" + self.passPhrase + "\t" + self.IP + "\t" + str(port[1]))
        login = login.encode('ascii')
        self.sendServerMessage(login)

    # Send the logoff message to the server
    def logoff(self):
        logoff = ("LOGOFF\t" + self.deviceID)
        logoff = logoff.encode('ascii')
        self.sendServerMessage(logoff)

    # Send data that is requested by the server
    def sendData(self, dcode, length, data, client):
        timeStamp = int(time())
        reply = ("DATA\t" + dcode + '\t' + self.deviceID + '\t' + str(timeStamp) + '\t' + str(length) + '\t' + data)
        reply = reply.encode('ascii')
        if client:
            self.sendClientMessage(reply,self.addr)
        else:
            self.sendServerMessage(reply)

    # This function processes the query message and will be fully implemented when more is known
    def processQuery(self, msg):
        if msg[1] == '01':
            dcode = "01"
            data = "Sensor Data"
            length = data.count(data)
            self.sendData(dcode, length, data, False)
        elif msg[1] == '99':
            dcode = "01"
            data = "Test Data"
            length = data.count(data)
            self.sendData(dcode, length, data, True)

    # This is a function to process the ACK message that comes from the server
    def processServerACK(self, msg):
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
        elif msg[1] == '21':
            print("Device did not exist")
        elif msg[1] == '30':
            print("Device is already registered with another MAC or IP")
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

    def processClientACK(self, msg):
        if msg[1] == '40':
            print("Status Received")
        if msg[1] == '50':
            print("Data Received")

    # Once a message is sent, this waits for a reply
    def processServerMessage(self):
        while True:
           # try:
                data = self.tcpClient.recv(1024)
                msg = data.decode('ascii')
                newMsg = msg.split('\t')
                if newMsg[0] == "QUERY":
                    print("got a query")
                    self.processQuery(newMsg)
                elif newMsg[0] == "ACK":
                    self.processServerACK(newMsg)
           # except:
             #   print("Connection is closed or unavailable")
            #    sys.exit(1)

    def processClientMessage(self):
        while True:
            data, self.addr = self.udpClient.recvfrom(1024)
            msg = data.decode('ascii')
            newMsg = msg.split('\t')
            if newMsg[0] == "QUERY":
                self.processQuery(newMsg)
            elif newMsg[0] == "ACK":
                self.processClientACK(newMsg)

    def sendServerMessage(self, msg):
        #try:
            self.tcpClient.send(msg)
        #except:
        #    print("Socket has been closed or Server is offline, closing connection")
         #   self.tcpClient.close()
        #    sys.exit(1)

    def sendClientMessage(self, msg, addr):
        self.udpClient.sendto(msg, addr)

    def serverconnect(self):
        #try:
            self.tcpClient.connect(self.server)
       # except:
           # print("Server is offline")
          #  sys.exit(1)

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
            device.logoff()
            break


def randomMAC():
    return [0x00, 0x16, 0x3e,
            randint(0x00, 0x7f),
            randint(0x00, 0xff),
            randint(0x00, 0xff)]

def MACprettyprint(mac):
    return ':'.join(map(lambda x: "%02x" % x, mac))


# Main function to run the program
def main():
    # Initialize the device with values
    mac = MACprettyprint(randomMAC())
    print (mac)
    device = IOTclient(args["device"], "toor", mac, int(args["port"]), args["server"])
    device.bindClient()
    device.serverconnect()
    tcpListener = Thread(target=device.processServerMessage, daemon=True)
    udpListener = Thread(target=device.processClientMessage, daemon=True)
    tcpListener.start()
    udpListener.start()
    mainMenu(device)
    tcpListener.join(1)
    udpListener.join(1)
    device.tcpClient.close()


if __name__ == "__main__":
    main()
