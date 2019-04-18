#!/usr/bin/env python3
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, gethostname, gethostbyname
import sqlite3
from time import time
from argparse import ArgumentParser
import hashlib
from threading import Thread
import logging

# Command line arguments for the port to start the server on
parser = ArgumentParser()
parser.add_argument("-p", "--port", required=True, help="The port that the server starts on")
args = vars(parser.parse_args())


class IOTCloudServer:
    tcpServer = socket(AF_INET, SOCK_STREAM)
    tcpServer.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    hostname = gethostname()
    TCP_IP = gethostbyname(hostname)
    TCP_PORT = 0
    connectionQueue = []
    threads = []

    print("Server at: ", TCP_IP)

    def __init__(self, p):
        self.TCP_PORT = p

    def startServer(self):
        self.tcpServer.bind((self.TCP_IP, self.TCP_PORT))

    def acceptConnection(self):
        while True:
            self.tcpServer.listen(5)
            (connect, (ip, port)) = self.tcpServer.accept()
            print("Connection from: %s:%s" % (ip, port))
            self.connectionQueue.append(connect)
            newthread = Thread(target=self.recieveData, args=(connect,), daemon=True)
            newthread.start()
            self.threads.append(newthread)

    def recieveData(self, connect):
        while True:
            data = connect.recv(2048)
            tempData = data.decode('ascii')
            msg = tempData.split('\t')
            self.processData(msg, connect)

    def processData(self, msg):
        conn = sqlite3.connect('IOTCloud.sqlite')
        cur = conn.cursor()
        if msg[0] == 'REGISTER':
            deviceID = msg[1]
            deviceName = msg[2]
            sql = '''INSERT INTO devicelist (deviceID, deviceName) VALUES(?,?)'''
            data = (deviceID, deviceName)
            cur.execute(sql, data)
            conn.commit()
        if msg[0] == 'DATA':
            deviceID = msg[1]
            sqlmsg = '''INSERT INTO messagebox (deviceID, message) VALUES (?,?)'''
            msg = (deviceID, msg[2])
            server = self.connectionQueue[0]

            cur.execute(sqlmsg, msg)
            conn.commit()
        conn.close()


def main():
    server = IOTCloudServer(int(args['port']))
    server.startServer()
    server.acceptConnection()
    #tcpListener = Thread(target=server.acceptConnection, daemon=True)
    #tcpListener.start()


if __name__ == "__main__":
    main()
