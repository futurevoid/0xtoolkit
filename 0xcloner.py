import os

git_input = input("git cmd: ") 
os.system(git_input)
os.system('pip install -r requirements.txt --break-system-packages')

#with open("requirements.txt", 'r') as f:
#    f.read()
