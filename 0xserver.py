import socket

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


host = socket.gethostname()
port = 4444

serversocket.bind((host, port))

serversocket.listen(3)

while True:
    clientsocket,addr = serversocket.accept()
    
    print(f"Connection from {addr} has been established!")
    
    clientsocket.send(bytes("Welcome to the server!", "utf-8"))
    clientsocket.close()