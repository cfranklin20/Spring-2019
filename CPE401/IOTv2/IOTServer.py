#!/usr/bin/env python3

# Program: An IOT Server implementation for University of Nevada, Reno CPE 401
# Filename: IOT Server.py
# Written By: Clayton Franklin
# Date Created: 27 Feb 2019
# Version: 1.0

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, gethostname, gethostbyname
import sqlite3
from time import time
from argparse import ArgumentParser
import hashlib
from threading import Thread
import queue

# Command line arguments for the port to start the server on
parser = ArgumentParser()
parser.add_argument("-p", "--port", required=True, help="The port that the server starts on")
args = vars(parser.parse_args())

menu = {"1": "Query Device", "0": "Close Server"}


class MyThread(Thread):
    def __init__(self):
        thread = Thread(target=self.run(), args=())
        thread.start()

    def run(self):
        print("test thread")


class IOTserver:
    tcpServer = socket(AF_INET, SOCK_STREAM)
    tcpServer.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    hostname = gethostname()
    TCP_IP = gethostbyname(hostname)
    TCP_PORT = 0
    print(TCP_IP)
    h = hashlib.sha256()
    addr = ''
    threads = []
    tcpListener = []
    connectionQueue = []
    # Take the command line port and give it to the server

    def __init__(self, p):
        self.TCP_PORT = p

    # Starts the server and connects to the Database
    def startServer(self):
        self.tcpServer.bind((self.TCP_IP, self.TCP_PORT))

    # Generates the ACK message to send to the device
    def ackMessage(self, code, deviceID, msg, connect):
        timeStamp = int(time())
        tempMsg = msg.encode('ascii')
        self.h.update(tempMsg)
        hashed = self.h.hexdigest()
        message = ("ACK\t" + code + '\t' + deviceID + '\t' + str(timeStamp) + '\t' + hashed)
        messageE = message.encode('ascii')
        connect.send(messageE)

    # Generates the query message for data requested by the server
    def queryMessage(self):
        code = "01"
        timeStamp = int(time())
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        sql = '''SELECT * FROM registration'''
        cur.execute(sql,)
        devices = cur.fetchall()
        i = 0
        print("Active Devices:")
        for device in range(len(devices)):
            if devices[device][6] == 1:
                i += 1
                print(i, ':', devices[device][1])

        if i >= 1:
            selection = input("Choose a device to query:")
        else:
            print("No Active Devices")
            return
        deviceID = "Server"
        param = devices[int(selection) - 1][1]
        connect = self.connectionQueue[int(selection) - 1]
        msg = ("QUERY\t" + code + "\t" + deviceID + "\t" + str(timeStamp) + "\t" + param)
        msg = msg.encode('ascii')
        connect.send(msg)
        cur.close()
        conn.close()

    # Registers the device into the database
    def registerDevice(self, data, connect):
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        device = self.lookup(data[1], '', '')
        # Check to see if the device is in the database
        if device[0]:
            msg = self.remakeString(data)
            # Check to see if the IP is already attached to another device
            # if device[1][0][4] == data[4] and device[1][0][1] != data[1]:
            #   self.ackMessage('12', data[1], msg, self.addr)

            # Check to see if the MAC address is attached to another device
            if device[1][0][3] == data[3] and device[1][0][1] != data[1]:
                self.ackMessage('13', data[1], msg, connect)

            # Update the IP if the IP is different but the device is the same
            # elif device[1][0][4] != data[4] and device[1][0][1] == data[1]:
            #    sql = "UPDATE registration SET ip=? WHERE deviceName=?"
            #    cur.execute(sql, (data[4], data[1]))
            #    self.ackMessage('02', data[1], msg, self.addr)

            # If all of these checks are passed, it is the same device trying to register
            else:
                self.ackMessage('01', data[1], msg, connect)

        # If the device is not in the database, check to make sure the mac and IP aren't being reused
        elif not device[0]:
            # ip = self.lookup('', data[4], '')
            mac = self.lookup('', '', data[3])
            msg = self.remakeString(data)

            # Checking if an ip exists in the database
            # if ip[0]:
            #    self.ackMessage('12', data[1], msg, self.addr)

            if mac[0]:
                self.ackMessage('13', data[1], msg, connect)

            # Device is not in the database, add it to the database
            # elif ip[0] == False and mac[0] == False:
            elif not mac[0]:
                # SQL command to add the device to the database
                sql = ''' INSERT INTO registration(deviceName, passphrase, mac, active) 
                             VALUES(?,?,?,?) '''
                insertData = (data[1], data[2], data[3], 0)
                cur.execute(sql, insertData)
                conn.commit()
                msg = self.remakeString(data)
                self.ackMessage('00', data[1], msg, connect)
                cur.close()
                conn.close()

    # Rejoins the original message back to its original form
    def remakeString(self, string):
        s = '\t'
        s = s.join(string)
        return s

    # This function removes a device from the database
    def deregisterDevice(self, data, connect):
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        deviceName = data[1]
        device = self.lookup(deviceName, '', '')
        # Check if the device is in the database
        if device[0]:
            sql = 'DELETE FROM registration where deviceName=?'
            cur.execute(sql, (deviceName,))
            conn.commit()
            msg = self.remakeString(data)
            self.ackMessage('20', data[1], msg, connect)
            cur.close()
            conn.close()

        # Device is not in the database
        elif not device[0]:
            msg = self.remakeString(data)
            self.ackMessage('21', data[1], msg, connect)

    # Looks up a device name, IP, or MAC in the database
    def lookup(self, deviceName, ip, mac):
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        # Get the number of rows in the table
        exists = False

        # Looks up the device name
        if deviceName:
            cur.execute("SELECT * FROM registration where deviceName=?", (deviceName,))
            rows = cur.fetchall()

            # If the device name does not exist the next query will be for IP
            if not rows:
                exists = False
                cur.close()
                conn.close()
                return exists, rows

            # Look for the device in the database
            else:
                for i in range(len(rows)):
                    if rows[i][1] == deviceName:
                        exists = True
        # Looks up the IP address
        elif ip:
            cur.execute("SELECT * FROM registration where ip=?", (ip,))
            rows = cur.fetchall()

            # If the IP does not exist, the next query will be for MAC address
            if not rows:
                exists = False
                cur.close()
                conn.close()
                return exists, rows
            else:
                for i in range(len(rows)):
                    if rows[i][4] == ip:
                        exists = True
        # Looks up the MAC address
        elif mac:
            cur.execute("SELECT * FROM registration where mac=?", (mac,))
            rows = cur.fetchall()

            # If the nex
            if not rows:
                exists = False
                cur.close()
                conn.close()
                return exists, rows
            else:
                for i in range(len(rows)):
                    if rows[i][3] == mac:
                        exists = True

        cur.close()
        conn.close()
        return exists, rows

    # Logs in the device
    def loginDevice(self, data, connect):
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        deviceName = data[1]
        ip = data[3]
        port = int(data[4])
        msg = self.remakeString(data)
        device = self.lookup(deviceName, '', '')

        # Changes the status of the device to active
        if device[0]:
            if device[1][0][2] == data[2] and device[1][0][6] == 0:
                sql = "UPDATE registration SET ip=?, port=?, active=? WHERE deviceName=?"
                update = (ip, port, 1, deviceName)
                cur.execute(sql, update)
                conn.commit()
                cur.close()
                conn.close()
                self.ackMessage('70', deviceName, msg, connect)
        else:
            self.ackMessage('31', deviceName, msg, connect)

    # Logs off the device from the server
    def logoffDevice(self, data, connect):
        conn = sqlite3.connect('IOT.db')
        cur = conn.cursor()
        deviceName = data[1]
        msg = self.remakeString(data)
        device = self.lookup(deviceName, '', '')
        if device[0]:
            if device[1][0][6] == 1:
                sql = "UPDATE registration SET active=? WHERE deviceName=?"
                update = (0, deviceName)
                cur.execute(sql, update)
                conn.commit()
                cur.close()
                conn.close()
                self.ackMessage('80', deviceName, msg, connect)
        else:
            self.ackMessage('31', deviceName, msg, connect)

    # Processes the message that the client sends
    def processMessage(self, data, connect):
        tempData = data.decode('ascii')
        msg = tempData.split('\t')
        if msg[0] == 'REGISTER':
            self.registerDevice(msg, connect)
        elif msg[0] == "DEREGISTER":
            self.deregisterDevice(msg, connect)
        elif msg[0] == "LOGIN":
            self.loginDevice(msg, connect)
        elif msg[0] == "LOGOFF":
            self.logoffDevice(msg, connect)
        elif msg[0] == "DATA":
            self.processData(msg, connect)
        elif msg[0] == "QUERY":
            self.processQuery(msg, connect)

    def processData(self, msg,connect):
        if msg[1] == '01':
            msgE = self.remakeString(msg)
            self.ackMessage("50", msg[2], msgE, connect)

    def processQuery(self, msg, connect):
        if msg[1] == '01':
            self.sendData(msg)

    def sendData(self,msg):

        self.lookup()

    # Listens on the port for data
    def acceptConnection(self):
        while True:
            self.tcpServer.listen(5)
            (connect, (ip, port)) = self.tcpServer.accept()
            self.connectionQueue.append(connect)
            newthread = Thread(target=self.recieveData, args=(connect,), daemon=True)
            newthread.start()
            self.threads.append(newthread)

    def recieveData(self, connect):
        while True:
            data = connect.recv(2048)
            self.processMessage(data, connect)

    # Menu for the server to send queries
    def menu(self):
        while True:
            options = menu.keys()
            print("Choose a function to perform:")
            for entry in options:
                print(entry, menu[entry])
            selection = input("Select an action:")
            if selection == '1':
                self.queryMessage()
            elif selection == '0':
                for t in self.threads:
                    t.join(1)
                break


def main():
    server = IOTserver(int(args["port"]))
    server.startServer()
    tcpListener = Thread(target=server.acceptConnection, daemon=True)
    tcpListener.start()
    server.menu()
    tcpListener.join(1)


if __name__ == "__main__":
    main()
