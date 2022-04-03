import socket

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverAddr = input("Server address: ")
port = int(input("port number: "))
filename = input("file name: ")
clientSocket.connect((serverAddr, port))
filename = "/"+filename
request = b'GET %s HTTP/1.1\r\nHost: %s:%s\r\n'%(filename.encode(), serverAddr.encode(), str(port).encode())
clientSocket.send(request)
content = b""
# data = clientSocket.recv(1024).decode()
# print(data)
while 1:
    data = clientSocket.recv(1024)
    content += data
    if len(data) < 1024:
        break

print(content.decode())