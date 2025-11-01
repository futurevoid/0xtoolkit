from halo import Halo
import subprocess
import time


first_time_check = input("first time to run 0xGPT ? (yes/no) :").lower()

if first_time_check == "yes": 
    
   

    subprocess.run(["pip", "install", "git+https://github.com/mmabrouk/chatgpt-wrapper","--break-system-packages"])

    subprocess.run(["playwright", "install", "firefox"])

    print("\nA window will open in a few seconds. Please log in it.")

    time.sleep(3)

    process = subprocess.Popen(["chatgpt", "install"])
    
    raise SystemExit
    
else:
    
    from chatgpt_wrapper import ChatGPT # type: ignore
    
    bot = ChatGPT()
    
    prompt = input("0xGPT>")
    
    spinner = Halo(text='Getting Stuff Together Bruv', spinner='dots')
    
    spinner.start()
    
    response = bot.ask(prompt)
    
    spinner.stop()
    
    print(response)
    
    spinner.succeed("All Done, Fam.")
    
    
    

