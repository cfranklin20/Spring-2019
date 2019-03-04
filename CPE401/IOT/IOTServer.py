#!/usr/bin/env python3

# Program: An IOT Server implementation for University of Nevada, Reno CPE 401
# Filename: IOT Server.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, getfqdn, AF_INET, SOCK_DGRAM
import sqlite3 as sq
from time import time
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-p", "--port", required=True, help="The port that the server starts on")
args = vars(parser.parse_args())

# ackcodes = {"00":}


class IOTserver:
    s = socket(AF_INET, SOCK_DGRAM)
    port = 0
    conn = sq.connect('IOT.db')
    cur = conn.cursor()

    def __init__(self, p):
        self.port = p

    def startServer(self):
        self.s.bind(('127.0.0.1', self.port))

    def ackMessage(self, code, deviceID, hashed, addr):
        time = int(time())
        message = ("ACK" + code + deviceID + time + hashed)
        self.s.sendto(message, addr)

    def queryMessage(self):
        print("Ask client for data")

    def registerDevice(self, data):
        device = self.lookup()


        insert = ''' INSERT into registration(deviceName, passphrase, mac, ip, port, active) 
        VALUES(?,?,?,?,?,?)'''
        insertData = (data[1], data[2], data[3], data[4], int(data[5]), 0)
        self.cur.execute(insert, insertData)

    def deregisterDevice(self,mac):
        drop = 'DELETE from registration where mac=?'
        mac ="AA:BB:CC:DD:EE:FF"
        self.cur.execute(drop, mac)

    def lookup(self, mac):
        select = "SELECT * from registration where mac=?"
        self.cur.execute(select, mac)
        data = self.cur.fetchall()

        return data

    def processData(self, data, addr):
        tempData = data.decode('ascii')
        msg = tempData.split('\t')
        print(msg[0])
        if msg[0] == 'REGISTER':
            self.registerDevice(msg)
        elif msg[0] == "DEREGISTER":
            self.deregisterDevice()
        elif msg[0] == "LOGIN":
            self.loginDevice()
        elif msg[0] == "LOGOFF":
            self.logoffDevice()

    def receiveData(self):
        print('server at', getfqdn(''))

        while True:
            data, addr = self.s.recvfrom(1024)
            print("Connection from", addr)
            self.processData(data, addr)


def main():
    server = IOTserver(int(args["port"]))
    server.startServer()
    server.receiveData()


if __name__ == "__main__":
    main()
