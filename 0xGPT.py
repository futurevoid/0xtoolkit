from halo import Halo
import subprocess
import psutil
import time

subprocess.run(["pip", "install", "git+https://github.com/mmabrouk/chatgpt-wrapper"])

subprocess.run(["playwright", "install", "firefox"])
print("A window will open in a few seconds. Please log in it.")
time.sleep(3)
process = subprocess.Popen(["chatgpt", "install"])
# User should log in to ChatGPT in the browser window

# Check if the process is running before killing it
if psutil.pid_exists(process.pid):
    process.kill()
else:
    print("Process not running")

subprocess.run(["chatgpt"])
