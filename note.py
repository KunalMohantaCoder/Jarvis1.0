import subprocess
import datetime
import os

def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(text)
    notepad = "C://Program Files (x86)//Notepad++//notepad++.exe"
    if os.path.exists(notepad):
        subprocess.Popen([notepad, file_name])
    else:
        os.startfile(file_name)
    return file_name

