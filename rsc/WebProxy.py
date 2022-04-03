import socket
import sys
import os
import time

# Create a server socket, bind it to a port and start listening
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSerPort = 8080
serverSock.bind(("", tcpSerPort))
print(tcpSerPort)
serverSock.listen(10)
while 1:
    # Start receiving data from the client
    print('Ready to serve...')
    clientSock, addr = serverSock.accept()
    print('Received a connection from:', addr)
    message = clientSock.recv(1024)
    print("message:", message)
    if message == b'':
        continue
    # Extract the filename from the given message
    first_line = message.split(b'\n')[0]
    method = first_line.split(b" ")[0]
    url = first_line.split(b" ")[1]
    print("url:", url)
    # Filter
    if method == b"POST":
        continue
    if url.find(b"fox") != -1:  # Firefox send many requests which include word "fox", I don't want that!
        continue
    http_pos = url.find(b"://")  # find pos of ://
    if http_pos == -1:
        temp = url
    else:
        temp = url[(http_pos + 3):]  # get the rest of url

    port_pos = temp.find(b":")  # find the port pos (when method==CONNECT, there exists port)
    filename = temp
    # find end of web server
    webserver_pos = temp.find(b"/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if port_pos == -1 or webserver_pos < port_pos:
        # default port
        port = 80
        webserver = temp[:webserver_pos]
    else:  # specific port
        port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
        webserver = temp[:port_pos]

    print("filename:", filename)
    try:
        # Check whether the file is in the cache
        f = open(b"Cache/" + filename, "rb")
        content = f.read()
        f.close()
        print("Cache Found")
        if method == b"CONNECT":
            header = b'HTTP/1.1 200 Connection established\n' + b'Proxy-agent: 1.0\n\n'
        else:
            header = b'HTTP/1.1 200 OK\r\n\r\n'
        content = header + content
        clientSock.sendall(content)
        print("Read from Cache")
    except IOError:
        try:
            proxySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect the socket to port
            print((webserver, port))
            proxySock.connect((webserver, port))
            proxySock.sendall(message)
            content = b""
            if method == b"CONNECT":
                start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                clientSock.sendall(b'HTTP/1.1 200 Connection established\n' + b'Proxy-agent: 1.0\n\n')
            while 1:
                data = proxySock.recv(2048)
                print("data:", data[:100])
                if len(data)<2048:
                    break
                else:
                    content += data
                    clientSock.send(data)
            # Create a new file in the cache to store the data received.
            filename = filename.decode()
            filename = "Cache/" + filename
            filesplit = filename.split('/')
            for i in range(0, len(filesplit) - 1):
                if not os.path.exists("/".join(filesplit[0:i + 1])):
                    os.makedirs("/".join(filesplit[0:i + 1]))
            cacheFile = open(filename, "wb")
            cacheFile.write(content)
            cacheFile.close()
        except Exception as e:
            print("Illegal request")
            print(e)
        proxySock.close()
    clientSock.close()
serverSock.close()
