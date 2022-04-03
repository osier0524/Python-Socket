#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys
import os
from _thread import *
import threading


def handleRequest(tcpSocket):
    while 1:
        # 1. Receive request message from the client on connection socket
        req = tcpSocket.recv(1024)
        # 2. Extract the path of the requested object from the message (second part of the HTTP header)
        if not req:
            break  # break if request is null
        print(req)
        print(req.split()[1])
        filename = req.split()[1]
        filename = filename[1:]
        #  3. Read the corresponding file from disk
        if os.path.exists(filename):
            f = open(filename, 'rb')
            # 4. Store in temporary buffer
            buffer = f.read()
            f.close()
            header = b'HTTP/1.1 200 OK\r\n\r\n'
            content = header + buffer
        else:
            # 5. Send the correct HTTP response error
            header = b'HTTP/1.1 404 Not Found'
            content = header
        # 6. Send the content of the file to the socket
        tcpSocket.sendall(content)
    # 7. Close the connection socket
    tcpSocket.close()

    pass  # Remove/replace when function is complete


def startServer(serverAddress, serverPort):
    # 1. Create server socket
    websocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 2. Bind the server socket to server address and server port
    websocket.bind((serverAddress, serverPort))
    # 3. Continuously listen for connections to server socket
    websocket.listen(5)
    # 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
    while 1:
        conn, addr = websocket.accept()
        thread = threading.Thread(target=handleRequest, args=(conn,))  # multithread
        thread.start()
        thread.join()
        print()
    #  5. Close server socket
    websocket.close()
    pass  # Remove/replace when function is complete


startServer("", 8080)
