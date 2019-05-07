#!/usr/bin/env python3

# Program: An IOT client implementation for University of Nevada, Reno CPE 401
# Filename: IOT Client.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, gethostbyname, gethostname
from threading import Thread, Timer
import sqlite3
import argparse as ap
import hashlib
import sys
from time import time
from random import randint

# Use Command Line arguments to get pertinent information
parser = ap.ArgumentParser()
parser.add_argument("-d", "--device", required=True, help="The name of the device")
parser.add_argument("-i", "--id", required=True, help="The deviceName for the cloud")
parser.add_argument("-s", "--server", required=True, help="The IP of the server")
parser.add_argument("-p", "--port", required=True, help="The port that the server is on")

args = vars(parser.parse_args())

# Menu options for the user to select
menu = {"1": "Register Device", "2": "Deregister Device",
        "3": "Login", "4": "Logoff", "5": "Query Client",
        "6": "Send to Cloud", "0": "Quit"}


# A Data Structure that holds all relevant functions pertaining to the
class IOTclient:
    # TCP Socket
    tcpClient = socket(AF_INET, SOCK_STREAM)
    # UDP Socket
    udpClient = socket(AF_INET, SOCK_DGRAM)
    # TCP Socket for AWS
    tcpAWS = socket(AF_INET, SOCK_STREAM)
    addr = ''
    # Class Variables
    hostname = gethostname()
    IP = gethostbyname(hostname)
    conn = sqlite3.connect("IOT.db")
    h = hashlib.sha256()
    AWS_IP = ''
    AWS_PORT = 0

    # Constructor for the Object
    def __init__(self, d, id, pp, m, p, s):
        self.deviceName = d
        self.deviceID = id
        self.passPhrase = pp
        self.MAC = m
        self.serverPort = p
        self.server = s, p

    # This binds the client to the listening port
    def bindClient(self):
        self.tcpClient.bind((self.IP, 0))
        self.udpClient.bind((self.IP, 0))
        self.tcpAWS.bind((self.IP, 0))

    # Send the register message to the server
    def register(self):
        reg = ("REGISTER\t" + self.deviceName + "\t" + self.passPhrase + "\t" + self.MAC)
        reg = reg.encode('ascii')
        self.sendServerMessage(reg)

    # Send the deregister message to the server
    def deregister(self):
        dereg = ("DEREGISTER\t" + self.deviceName + "\t" + self.passPhrase + "\t" + self.MAC)
        dereg = dereg.encode('ascii')
        self.sendServerMessage(dereg)

    # Send the login message to the server
    def login(self):
        port = self.udpClient.getsockname()
        login = ("LOGIN\t" + self.deviceName + "\t" + self.passPhrase + "\t" + self.IP + "\t" + str(port[1]))
        login = login.encode('ascii')
        self.sendServerMessage(login)

    # Send the logoff message to the server
    def logoff(self):
        logoff = ("LOGOFF\t" + self.deviceName)
        logoff = logoff.encode('ascii')
        self.sendServerMessage(logoff)

    # Send data that is requested by the server
    def sendData(self, dcode, length, data, client):
        timeStamp = int(time())
        reply = ("DATA\t" + dcode + '\t' + self.deviceName + '\t' + str(timeStamp) + '\t' + str(length) + '\t' + data)
        reply = reply.encode('ascii')
        if client:
            self.sendClientMessage(reply, self.addr)
        else:
            self.sendServerMessage(reply)

    def queryDevice(self):
        timeStamp = int(time())
        cur = self.conn.cursor()
        sql = '''SELECT * FROM registration where active=?'''
        cur.execute(sql, (1,))
        devices = cur.fetchall()
        if len(devices) > 0:
            print("Active Devices: * denotes current device")
            i = 0
            for device in range(len(devices)):
                if devices[device][1] == self.deviceName:
                    print(i + 1, ':', devices[device][1], "*")
                    i += 1
                else:
                    print(i + 1, ':', devices[device][1])
                    i += 1
            selection = input("Choose a device to query:")
        else:
            print("No Active Devices")
            return
        addr = (devices[int(selection) - 1][4], devices[int(selection) - 1][5])
        param = devices[int(selection) - 1][1]
        code = "01"
        msg = ("QUERY\t" + code + "\t" + self.deviceName + "\t" + str(timeStamp) + "\t" + param)
        msgE = msg.encode('ascii')
        self.sendClientMessage(msgE, addr)

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

    def checkStatus(self, addr):
        while True:
            print ("Entering Timer")
            timer = Timer(5.0, self.sendStatus, args=[addr])
            timer.start()

    def sendStatus(self, addr):
        timeStamp = int(time)
        message = "Checking Status"
        length = len(message)
        scode = "01"
        msg = ("STATUS\t" + scode + "\t" + self.deviceName + "\t" + str(timeStamp)
               + "\t" + str(length) + "\t" + message)
        msgE = msg.encode('ascii')
        self.udpClient.sendto(msgE, addr)

    def clientACK(self, addr, code, msg):
        timeStamp = int(time())
        msg = self.remakeString(msg)
        tempMsg = msg.encode('ascii')
        self.h.update(tempMsg)
        hashed = self.h.hexdigest()
        message = ("ACK\t" + code + '\t' + self.deviceName + '\t' + str(timeStamp) + '\t' + hashed)
        messageE = message.encode('ascii')
        self.udpClient.sendto(messageE, addr)

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
            try:
                data = self.tcpClient.recv(1024)
                msg = data.decode('ascii')
                newMsg = msg.split('\t')
                if newMsg[0] == "QUERY":
                    self.processQuery(newMsg)
                elif newMsg[0] == "ACK":
                    self.processServerACK(newMsg)
                elif newMsg[0] == "DATA":
                    self.processServerData(newMsg)
            except:
                print("Connection is closed or unavailable")
                sys.exit(1)

    def processClientMessage(self):
        while True:
            data, addr = self.udpClient.recvfrom(1024)
            print("Recieved connection from: ", addr)
            #self.checkStatus(addr)
            msg = data.decode('ascii')
            newMsg = msg.split('\t')
            if newMsg[0] == "QUERY":
                self.processQuery(newMsg)
            elif newMsg[0] == "ACK":
                self.processClientACK(newMsg)
            elif newMsg[0] == "DATA":
                self.clientACK(addr, "50", newMsg)
            elif newMsg == "STATUS":
                self.clientACK(addr, "40", newMsg)

    def sendServerMessage(self, msg):
        try:
            self.tcpClient.send(msg)
        except:
            print("Socket has been closed or Server is offline, closing connection")
            self.tcpClient.close()
            sys.exit(1)

    def sendClientMessage(self, msg, addr):
        self.udpClient.sendto(msg, addr)

    def serverconnect(self):
        try:
            self.tcpClient.connect(self.server)
        except:
            print("Server is offline")
            sys.exit(1)

    def remakeString(self, string):
        s = '\t'
        s = s.join(string)
        return s

    def processServerData(self, msg):
        if msg[1] == '02':
            self.AWS_IP = msg[2]
            print("AWS IP and Port: %s:%s" % (self.AWS_IP, self.AWS_PORT))
            self.AWS_PORT = int(msg[3])
            self.tcpAWS.connect((self.AWS_IP, self.AWS_PORT))
            msg = "REGISTER\t" + self.deviceID + "\t" + self.deviceName
            msgE = msg.encode('ascii')

    def sendCloud(self):
        data = input("Enter a message to send to the cloud: ")
        msg = "DATA\t" + self.deviceID + "\t" + data
        msgE = msg.encode('ascii')
        self.tcpAWS.send(msgE)


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
        elif selection == '5':
            device.queryDevice()
        elif selection == '6':
            device.sendCloud()
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
    device = IOTclient(args["device"], args["id"], "toor", mac, int(args["port"]), args["server"])
    device.bindClient()
    device.serverconnect()
    tcpListener = Thread(target=device.processServerMessage, daemon=True)
    udpListener = Thread(target=device.processClientMessage, daemon=True)
    tcpListener.start()
    udpListener.start()
    mainMenu(device)
    tcpListener.join(0.1)
    udpListener.join(0.1)
    device.tcpClient.close()


if __name__ == "__main__":
    main()
