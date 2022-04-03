#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages

MAX_HOPS = 30
TRIES = 3


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, traceType):
    # 1. Wait for the socket to receive a reply
    timeleft = timeout
    while True:
        timeStart = time.time()
        selected = select.select([icmpSocket], [], [], timeleft)
        # 2. Once received, record time of receipt, otherwise, handle a timeout
        if not selected[0]:
            return
        timeReceive = time.time()
        # 3. Compare the time of receipt to time of sending, producing the total network delay
        delay = timeReceive - timeStart
        # 4. Unpack the packet header for useful information, including the ID
        recPacket, addr = icmpSocket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type, code, checksum, receiverID, seqNum = struct.unpack("bbHHh", icmpHeader)
        # 5. Check ICMP type
        if traceType == "ICMP":
            if type == 11 and code == 0:
                # 6. Return total network delay
                return delay, addr, 0
            elif type == 0:
                return delay, addr, 1
        elif traceType == "UDP":
            if type == 11 and code == 0:
                # 6. Return total network delay
                return delay, addr, 0
            elif type == 3 and code == 3:
                return delay, addr, 1

    pass  # Remove/replace when function is complete


def sendOnePing(icmpSocket, destinationAddress, ID, type):
    # 1. Build ICMP header, which is type(8), checksum(16), id(16), sequence(16)
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # 2. Checksum ICMP packet using given function
    myChecksum = checksum(header + data)
    # 3. Insert checksum into packet
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    # 4. Send packet using socket
    startTime = time.time()
    if type == "ICMP":
        icmpSocket.sendto(packet, (destinationAddress, 1))
    if type == "UDP":
        icmpSocket.sendto(packet, (destinationAddress, 6666))
    #  5. Record time of sending
    timeSent = time.time() - startTime
    pass  # Remove/replace when function is complete


def doOnePing(destinationAddress, timeout, ttl):
    # 1. Create ICMP socket
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    mySocket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
    mySocket.settimeout(1)
    ID = os.getpid() & 0xFFFF
    # 2. Call sendOnePing function
    sendOnePing(mySocket, destinationAddress, ID, "ICMP")
    # 3. Call receiveOnePing function
    delay, addr, info = receiveOnePing(mySocket, destinationAddress, ID, timeout, "ICMP")
    # 4. Close ICMP socket
    mySocket.close()
    # 5. Return total network delay
    return delay, addr, info
    pass  # Remove/replace when function is complete


def UDPdoOnePing(destinationAddress, timeout, ttl):
    # 1. Create ICMP socket
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sendSocket.setsockopt(socket.SOL_IP, socket.IP_TTL, struct.pack('I', ttl))
    sendSocket.settimeout(2)
    recvSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('I', ttl))
    recvSocket.settimeout(2)
    recvSocket.bind(("", 6666))
    ID = os.getpid() & 0xFFFF
    # 2. Call sendOnePing function
    sendOnePing(sendSocket, destinationAddress, ID, "UDP")
    sendSocket.close()
    # 3. Call receiveOnePing function
    delay, addr, info = receiveOnePing(recvSocket, destinationAddress, ID, timeout, "UDP")
    recvSocket.close()
    # 5. Return total network delay
    return delay, addr, info
    pass  # Remove/replace when function is complete


def traceroute(host, timeout=1, maxHops=10, type="ICMP"):
    count = 0
    hostID = socket.gethostbyname(host)
    print("traceroute to %s(%s), %d hops max" % (host, hostID, maxHops))
    for ttl in range(1, maxHops + 1):
        print('{:>2d}'.format(ttl), end="")
        addr = None
        for i in range(TRIES):
            try:
                if type == "ICMP":
                    delay, address, info = doOnePing(hostID, timeout, ttl)
                if type == "UDP":
                    delay, address, info = UDPdoOnePing(hostID, timeout, ttl)
            except TypeError:
                delay = 0
                address = None
                info = 0
            addr = address
            if delay is None or delay == 0:
                print('      *      ', end="")
                count += 1
            else:
                delay = round(delay * 1000.0, 4)
                time.sleep(1)
                # print(' %f ms '%(delay),end="")
                print('{:>10.4f} ms'.format(delay), end='')
            if info == 1:
                break
        if addr == None:
            print('    Timeout')
        else:
            try:
                hostname = socket.gethostbyaddr(addr[0])
            except socket.error:
                print("    " + addr[0])
            else:
                print("    " + addr[0] + "(" + hostname[0] + ")")
    print("Finished:)")
    lossrate = count / (maxHops * TRIES)
    print("packet loss: %f%%" % (lossrate * 100))


type = input("ICMP or UDP? ").upper()
traceroute("www.baidu.com", 1, 30, type)
