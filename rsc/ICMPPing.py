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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
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
        # 5. Check that the ID matches between the request and reply
        if receiverID == ID:
            # 6. Return total network delay
            return delay
        elif type == 3 and code == 0:
            return 30  # network unreachable
        elif type == 3 and code == 1:
            return 31  # host unreachable
        elif type == 3 and code == 3:
            return 33  # port unreachable
        else:
            return
    pass  # Remove/replace when function is complete


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header, which is type(8), checksum(16), id(16), sequence(16)
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # 2. Checksum ICMP packet using given function
    myChecksum = checksum(header + data)
    # 3. Insert checksum into packet
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    # 4. Send packet using socket
    packet = header + data
    startTime = time.time()
    icmpSocket.sendto(packet, (destinationAddress, 1))
    #  5. Record time of sending
    timeSent = time.time() - startTime
    pass  # Remove/replace when function is complete


def doOnePing(destinationAddress, timeout):
    # 1. Create ICMP socket
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    ID = os.getpid() & 0xFFFF
    # 2. Call sendOnePing function
    sendOnePing(mySocket, destinationAddress, ID)
    # 3. Call receiveOnePing function
    delay = receiveOnePing(mySocket, destinationAddress, ID, timeout)
    # 4. Close ICMP socket
    mySocket.close()
    # 5. Return total network delay
    return delay
    pass  # Remove/replace when function is complete


def ping(host, timeout=1, tries=5):
    delay_list = [None for i in range(tries)]
    avgdelay = 0.0
    count = 0
    # 1. Look up hostname, resolving it to an IP address
    ipaddress = socket.gethostbyname(host)
    print("Ping " + ipaddress + ": ")
    print("")
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    for i in range(0, tries):
        delay = doOnePing(ipaddress, timeout)
        if delay == None:
            print("   *   Timeout")
        elif delay == 30:
            print("Destination Network Unreachable")
        elif delay == 31:
            print("Destination Host Unreachable")
        elif delay == 33:
            print("Destination Port Unreachable")
        else:
            print("Delay: ", end="")
            delay = round(delay * 1000.0, 4)
            print("%f ms" % (delay))
            avgdelay += delay
            count += 1
            delay_list[count-1] = delay
            time.sleep(1)

    if count != 0:
        avgdelay = avgdelay / count
        lossrate = (tries - count) / tries
        delay_list = delay_list[:count]
        print(delay_list)
        mindelay = min(delay_list)
        maxdelay = max(delay_list)
        print("minimum delay: %f, maximum delay: %f, average delay: %f" % (mindelay, maxdelay, avgdelay))
        print("packet loss: %d%%" % (lossrate * 100))
    pass  # Remove/replace when function is complete


host = input("Ping ")
change = input("Change parameters?(Y/N) ").upper()
if change == "Y":
    tries = int(input("Set measurement count: "))
    timeout = int(input("Set timeout: "))
    ping(host, timeout, tries)
else:
    ping(host)