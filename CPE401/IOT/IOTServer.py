#!/usr/bin/env python3

# Program: An IOT Server implementation for University of Nevada, Reno CPE 401
# Filename: IOT Server.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, getfqdn, AF_INET, SOCK_DGRAM
import sqlite3
from time import time
from argparse import ArgumentParser
import hashlib

# Command line arguments for the port to start the server on
parser = ArgumentParser()
parser.add_argument("-p", "--port", required=True, help="The port that the server starts on")
args = vars(parser.parse_args())

class IOTserver:
    s = socket(AF_INET, SOCK_DGRAM)
    port = 0
    conn = ''
    h = hashlib.sha256()
    addr = ''

    def __init__(self, p):
        self.port = p

    def startServer(self):
        self.s.bind(('127.0.0.1', self.port))
        self.conn = sqlite3.connect('IOT.db')

    def ackMessage(self, code, deviceID, msg, addr):
        timeStamp = int(time())
        tempMsg = msg.encode('ascii')
        self.h.update(tempMsg)
        hashed = self.h.hexdigest()
        message = ("ACK\t" + code + '\t' + deviceID + '\t' + str(timeStamp) + '\t' + hashed)
        messageE = message.encode('ascii')
        self.s.sendto(messageE, addr)

    def queryMessage(self):
        code = "0"
        timeStamp = int(time())
        msg = ("QUERY\t" + code + deviceID + str(timeStamp) + param)
        msg = msg.encode('ascii')
        self.s.sendto(msg, self.addr)

    def registerDevice(self, data, conn):
        cur = conn.cursor()
        device = self.lookup(data[1])

        if device[0] == True:
            msg = self.remakeString(data)
            if device[1][0][4] == data[4] and device[1][0][1] != data[1]:
                self.ackMessage('12', data[1], msg, self.addr)

            elif device[1][0][3] == data[3] and device[1][0][1] != data[1]:
                self.ackMessage('13', data[1], msg, self.addr)

            elif device[1][0][4] != data[4] and device[1][0][1] == data[1]:
                sql = "UPDATE registration SET ip=? WHERE deviceName=?"
                cur.execute(sql, (data[4], data[1]))
                self.ackMessage('02', data[1], msg, self.addr)
            else:
                self.ackMessage('01', data[1], msg, self.addr)
        elif device[0] == False:
            sql = ''' INSERT INTO registration(deviceName, passphrase, mac, ip, port, active) 
                         VALUES(?,?,?,?,?,?) '''
            insertData = (data[1], data[2], data[3], data[4], int(data[5]), 0)
            cur.execute(sql, insertData)
            conn.commit()
            msg = self.remakeString(data)
            self.ackMessage('00', data[1], msg, self.addr)

    def remakeString(self, string):
        s = '\t'
        s = s.join(string)
        return s

    def deregisterDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        device = self.lookup(deviceName)
        if device[0] == True:
            sql = 'DELETE FROM registration where deviceName=?'
            cur.execute(sql, (deviceName,))
            conn.commit()
            msg = self.remakeString(data)
            self.ackMessage('20', data[1], msg, self.addr)
        elif device[0] == False:
            msg = self.remakeString(data)
            self.ackMessage('21', data[1], msg, self.addr)

    def lookup(self, deviceName):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM registration where deviceName=?", (deviceName,))
        rows = cur.fetchall()
        # Get the number of rows in the table
        rowsQuery = "SELECT Count() FROM registration"
        cur.execute(rowsQuery)
        numberOfRows = cur.fetchone()[0]

        exists = False
        for i in range(numberOfRows):
            if rows[i][1] == deviceName:
                exists = True
        return exists, rows

    def loginDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        msg = self.remakeString(data)
        device = self.lookup(deviceName)
        if device[0] == True:
            if device[1][0][2] == data[2] and device[1][0][6] == 0:
                sql = "UPDATE registration SET active=? WHERE deviceName=?"
                update = (1, deviceName)
                cur.execute(sql, update)
                conn.commit()
                self.ackMessage('70', deviceName, msg, self.addr)
        else:
            self.ackMessage('31', deviceName, msg, self.addr)

    def logoffDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        msg = self.remakeString(data)
        device = self.lookup(deviceName)
        if device[0] == True:
            if device[1][0][6] == 1:
                sql = "UPDATE registration SET active=? WHERE deviceName=?"
                update = (0, deviceName)
                cur.execute(sql, update)
                conn.commit()
                self.ackMessage('80', deviceName, msg, self.addr)
        else:
            self.ackMessage('31', deviceName, msg, self.addr)

    def processData(self, data):
        tempData = data.decode('ascii')
        msg = tempData.split('\t')
        if msg[0] == 'REGISTER':
            self.registerDevice(msg, self.conn)
        elif msg[0] == "DEREGISTER":
            self.deregisterDevice(msg, self.conn)
        elif msg[0] == "LOGIN":
            self.loginDevice(msg, self.conn)
        elif msg[0] == "LOGOFF":
            self.logoffDevice(msg, self.conn)

    def receiveData(self):
        print('server at', getfqdn(''))

        while True:
            data, addr = self.s.recvfrom(1024)
            print("Connection from", addr)
            self.addr = addr
            self.processData(data)


def main():
    server = IOTserver(int(args["port"]))
    server.startServer()
    server.receiveData()



if __name__ == "__main__":
    main()
