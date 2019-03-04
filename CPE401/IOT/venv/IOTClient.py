#!/usr/bin/env python3

# Program: An IOT client implementation for University of Nevada, Reno CPE 401
# Filename: IOT Client.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_DGRAM
import os
import sys
import argparse as ap
import datetime

parser = ap.ArgumentParser()
parser.add_argument("-d","--device-name",required=True, help="The name of the device")
parser.add_argument("-s","--server",required=True, help="The IP of the server")
parser.add_argument("-p","--port",required=True, help="The port that the server is on")

args = vars(parser.parse_args())

# A Data Structure that holds all relevant functions pertaining to the
class client:

    s = socket(AF_INET, SOCK_DGRAM)
    server = (args["server"],args["port"])
    deviceID = args["device-name"]
    passPhrase = ''
    MAC = ''
    IP = ''
    port = ''

    def __init__(self,pp,m,i):
        self.passPhrase = pp
        self.MAC = m
        self.IP = i

    # Bind the socket to a port given by the OS
    def connection(self):
        s.bind(('127.0.0.1', 0))

    # Send the register message to the server
    def register(self):
        reg = ("REGISTER\t" + deviceID + "\t" + passPhrase + "\t" + MAC + "\t" + IP + "\t" + port)
        s.sendto(reg, server)

    # Send the deregister message to the server
    def deregister(self):
        dereg = ("DEREGISTER\t" + deviceID + "\t" + passPhrase + "\t" + MAC + "\t" + IP + "\t" + port)
        s.sendto(dereg, server)
        s.close()

    # Send the login message to the server
    def login(self):
        connection()
        login = ("LOGIN\t" + deviceID + "\t" + passPhrase + "\t" + IP + "\t" + port)
        s.sendto(login, server)

    # Send the logoff message to the server
    def logoff(self):
        logoff = ("LOGOFF\t" + deviceID)
        s.sendto(logoff, server)
        s.close()

    # Send data that is requested by the server
    def sendData(self):
        data =

    def processData(self):
        data, addr = s.recvfrom(1024)
        Dcode
        print ("received", data, "from", addr)
