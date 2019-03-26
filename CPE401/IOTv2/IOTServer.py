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

    # Take the command line port and give it to the server
    def __init__(self, p):
        self.port = p

    # Starts the server and connects to the Database
    def startServer(self):
        self.s.bind(('127.0.0.1', self.port))
        self.conn = sqlite3.connect('IOT.db')

    # Generates the ACK message to send to the device
    def ackMessage(self, code, deviceID, msg, addr):
        timeStamp = int(time())
        tempMsg = msg.encode('ascii')
        self.h.update(tempMsg)
        hashed = self.h.hexdigest()
        message = ("ACK\t" + code + '\t' + deviceID + '\t' + str(timeStamp) + '\t' + hashed)
        messageE = message.encode('ascii')
        self.s.sendto(messageE, addr)

    # Generates the query message for data requested by the server
    def queryMessage(self):
        code = "0"
        timeStamp = int(time())
        msg = ("QUERY\t" + code + deviceID + str(timeStamp) + param)
        msg = msg.encode('ascii')
        self.s.sendto(msg, self.addr)

    # Registers the device into the database
    def registerDevice(self, data, conn):
        cur = conn.cursor()
        device = self.lookup(data[1], '', '')
        # Check to see if the device is in the database
        if device[0] == True:
            msg = self.remakeString(data)
            # Check to see if the IP is already attached to another device
            if device[1][0][4] == data[4] and device[1][0][1] != data[1]:
                self.ackMessage('12', data[1], msg, self.addr)

            # Check to see if the MAC address is attached to another device
            elif device[1][0][3] == data[3] and device[1][0][1] != data[1]:
                self.ackMessage('13', data[1], msg, self.addr)

            # Update the IP if the IP is different but the device is the same
            elif device[1][0][4] != data[4] and device[1][0][1] == data[1]:
                sql = "UPDATE registration SET ip=? WHERE deviceName=?"
                cur.execute(sql, (data[4], data[1]))
                self.ackMessage('02', data[1], msg, self.addr)

            # If all of these checks are passed, it is the same device trying to register
            else:
                self.ackMessage('01', data[1], msg, self.addr)

        # If the device is not in the database, check to make sure the mac and IP aren't being reused
        elif device[0] == False:
            ip = self.lookup('', data[4], '')
            mac = self.lookup('', '', data[3])
            msg = self.remakeString(data)

            # Checking if an ip exists in the database
            if ip[0] == True:
                self.ackMessage('12', data[1], msg, self.addr)

            elif mac[0] == True:
                self.ackMessage('13', data[1], msg, self.addr)

            # Device is not in the database, add it to the database
            elif ip[0] == False and mac[0] == False:
                # SQL command to add the device to the database
                sql = ''' INSERT INTO registration(deviceName, passphrase, mac, ip, port, active) 
                             VALUES(?,?,?,?,?,?) '''
                insertData = (data[1], data[2], data[3], data[4], int(data[5]), 0)
                cur.execute(sql, insertData)
                conn.commit()
                msg = self.remakeString(data)
                self.ackMessage('00', data[1], msg, self.addr)

    # Rejoins the original message back to its original form
    def remakeString(self, string):
        s = '\t'
        s = s.join(string)
        return s

    # This function removes a device from the database
    def deregisterDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        device = self.lookup(deviceName, '', '')
        # Check if the device is in the database
        if device[0] == True:
            sql = 'DELETE FROM registration where deviceName=?'
            cur.execute(sql, (deviceName,))
            conn.commit()
            msg = self.remakeString(data)
            self.ackMessage('20', data[1], msg, self.addr)

        # Device is not in the database
        elif device[0] == False:
            msg = self.remakeString(data)
            self.ackMessage('21', data[1], msg, self.addr)

    # Looks up a device name, IP, or MAC in the database
    def lookup(self, deviceName, ip, mac):
        cur = self.conn.cursor()
        # Get the number of rows in the table
        exists = False

        # Looks up the device name
        if deviceName:
            cur.execute("SELECT * FROM registration where deviceName=?", (deviceName,))
            rows = cur.fetchall()

            # If the device name does not exist the next query will be for IP
            if not rows:
                exists = False
                return exists, rows

            # Look for the device in the database
            else:
                for i in range(len(rows)):
                    if rows[i][1] == deviceName:
                        exists = True

        # Looks up the IP address
        if ip:
            cur.execute("SELECT * FROM registration where ip=?", (ip,))
            rows = cur.fetchall()

            # If the IP does not exist, the next query will be for MAC address
            if not rows:
                exists = False
                return exists, rows
            else:
                for i in range(len(rows)):
                    if rows[i][4] == ip:
                        exists = True

        # Looks up the MAC address
        if mac:
            cur.execute("SELECT * FROM registration where mac=?", (mac,))
            rows = cur.fetchall()

            # If the nex
            if not rows:
                exists = False
                return exists, rows
            else:
                for i in range(len(rows)):
                    if rows[i][3] == mac:
                        exists = True

        return exists, rows

    # Logs in the device
    def loginDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        msg = self.remakeString(data)
        device = self.lookup(deviceName, '', '')

        # Changes the status of the device to active
        if device[0] == True:
            if device[1][0][2] == data[2] and device[1][0][6] == 0:
                sql = "UPDATE registration SET active=? WHERE deviceName=?"
                update = (1, deviceName)
                cur.execute(sql, update)
                conn.commit()
                self.ackMessage('70', deviceName, msg, self.addr)
        else:
            self.ackMessage('31', deviceName, msg, self.addr)

    # Logs off the device from the server
    def logoffDevice(self, data, conn):
        cur = conn.cursor()
        deviceName = data[1]
        msg = self.remakeString(data)
        device = self.lookup(deviceName, '', '')
        if device[0] == True:
            if device[1][0][6] == 1:
                sql = "UPDATE registration SET active=? WHERE deviceName=?"
                update = (0, deviceName)
                cur.execute(sql, update)
                conn.commit()
                self.ackMessage('80', deviceName, msg, self.addr)
        else:
            self.ackMessage('31', deviceName, msg, self.addr)

    # Processes the message that the client senf
    def processMessage(self, data):
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
        elif msg[0] == "DATA":
            self.processData(msg, self.conn)

    # Listens on the port for data
    def receiveData(self):
        print('server at', getfqdn(''))

        while True:
            data, addr = self.s.recvfrom(1024)
            print("Connection from", addr)
            self.addr = addr
            self.processMessage(data)


def main():
    server = IOTserver(int(args["port"]))
    server.startServer()
    server.receiveData()


if __name__ == "__main__":
    main()
