import datetime
import os
import random
import re
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
import urllib.parse
import webbrowser

import requests

from __init__ import JarvisAssistant
import config


obj = JarvisAssistant()

GREETINGS = {
    "hello jarvis",
    "jarvis",
    "wake up jarvis",
    "you there jarvis",
    "time to work jarvis",
    "hey jarvis",
    "ok jarvis",
    "are you there",
}
GREETINGS_RES = [
    "Always there for you.",
    "I am ready.",
    "Your wish is my command.",
    "How can I help?",
    "I am online and ready.",
]

EMAIL_DIC = {
    "myself": getattr(config, "email", ""),
    "my official email": getattr(config, "email", ""),
    "my second email": getattr(config, "email", ""),
    "my official mail": getattr(config, "email", ""),
    "my second mail": getattr(config, "email", ""),
}


def speak(text):
    obj.tts(text)


def _config_value(name):
    value = getattr(config, name, "")
    if not value or str(value).startswith("<"):
        return None
    return value


def computational_intelligence(question):
    app_id = _config_value("wolframalpha_id")
    if app_id:
        try:
            import wolframalpha

            client = wolframalpha.Client(app_id)
            answer = client.query(question)
            return next(answer.results).text
        except Exception as exc:
            return f"I could not fetch a WolframAlpha answer: {exc}"

    expression = re.sub(r"^(calculate|what is)\s+", "", question).strip()
    local_answer = obj.calculate_locally(expression)
    if local_answer is not None:
        return local_answer
    return "WolframAlpha needs an app id in config.py for that question."


def startup_message():
    now = obj.tell_time()
    return f"{obj.greeting()}. I am Jarvis, online and ready. Current time is {now}."


def process_command(command):
    command = command.strip().lower()
    if not command:
        return "Please enter a command."

    if command in GREETINGS:
        return random.choice(GREETINGS_RES)

    if "date" in command:
        return obj.tell_me_date()

    if "time" in command:
        return f"The time is {obj.tell_time()}."

    if command.startswith("launch "):
        apps = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
        }
        app = command.replace("launch ", "", 1).strip()
        path = apps.get(app, app)
        if obj.launch_any_app(path):
            return f"Launching {app}."
        return f"I could not launch {app}. Add its full path or check that it is installed."

    if command.startswith("open "):
        domain = command.replace("open ", "", 1).strip()
        opened = obj.website_opener(domain)
        return f"Opening {opened}." if opened else f"I could not open {domain}."

    if "weather" in command:
        city = command.split()[-1]
        return obj.weather(city)

    if command.startswith("tell me about "):
        topic = command.replace("tell me about ", "", 1).strip()
        return obj.tell_me(topic) or "I could not find that topic."

    if "news" in command or "headlines" in command:
        articles = obj.news()
        if not articles:
            return "I could not fetch the news right now."
        titles = [article.get("title", "") for article in articles[:5] if article.get("title")]
        return "Top headlines:\n" + "\n".join(f"- {title}" for title in titles)

    if "search google for" in command:
        url = obj.search_anything_google(command)
        return f"Searching Google: {url}"

    if command.startswith("youtube ") or command.startswith("play "):
        query = re.sub(r"^(youtube|play)\s+", "", command).strip()
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        webbrowser.open(url)
        return f"Opening YouTube results for {query}."

    if "email" in command or "send email" in command:
        sender_email = _config_value("email")
        sender_password = _config_value("email_password")
        if not sender_email or not sender_password:
            return "Email needs your address and app password in config.py."
        return "Email is configured. Use the voice flow for recipient, subject, and message."

    if command.startswith("calculate ") or command.startswith("what is ") or command.startswith("who is "):
        return computational_intelligence(command)

    if "make a note" in command or "write this down" in command or "remember this" in command:
        note_text = re.sub(r"^(make a note|write this down|remember this)\s*", "", command).strip()
        if not note_text:
            return "Tell me what to write after the note command."
        file_name = obj.take_note(note_text)
        return f"I made a note: {file_name}"

    if "joke" in command:
        try:
            import pyjokes

            return pyjokes.get_joke()
        except Exception:
            return "Jokes need the pyjokes package installed."

    if "system" in command:
        try:
            return obj.system_info()
        except Exception as exc:
            return f"System stats need psutil installed: {exc}"

    if command.startswith("where is "):
        place = command.replace("where is ", "", 1).strip()
        try:
            _current_loc, target_loc, distance = obj.location(place)
            city = target_loc.get("city", "")
            state = target_loc.get("state", "")
            country = target_loc.get("country", "")
            if city:
                return f"{place} is in {state}, {country}. It is about {distance} km away."
            return f"{place} is in {country}. It is about {distance} km away."
        except Exception as exc:
            return f"I could not find that location: {exc}"

    if "ip address" in command:
        try:
            ip = requests.get("https://api.ipify.org", timeout=10).text
            return f"Your IP address is {ip}."
        except Exception as exc:
            return f"I could not fetch the IP address: {exc}"

    if "where i am" in command or "current location" in command or "where am i" in command:
        try:
            city, state, country = obj.my_location()
            return f"You are currently in {city}, {state}, {country}."
        except Exception as exc:
            return f"I could not fetch your current location: {exc}"

    if "take screenshot" in command or "capture the screen" in command:
        try:
            import pyautogui

            file_name = f"screenshot-{datetime.datetime.now():%Y%m%d-%H%M%S}.png"
            pyautogui.screenshot().save(file_name)
            return f"Screenshot saved as {file_name}."
        except Exception as exc:
            return f"Screenshots need pyautogui working correctly: {exc}"

    if "goodbye" in command or "offline" in command or command == "bye":
        return "Goodbye. Jarvis is going offline."

    return "I did not recognize that command yet."


class JarvisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS")
        self.geometry("900x620")
        self.minsize(720, 480)
        self.configure(bg="#06090d")

        self.output = scrolledtext.ScrolledText(
            self,
            bg="#08111a",
            fg="#eaf6ff",
            insertbackground="#eaf6ff",
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=16, pady=(16, 8))

        controls = tk.Frame(self, bg="#06090d")
        controls.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.entry = tk.Entry(
            controls,
            bg="#101d29",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Segoe UI", 12),
            relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10)
        self.entry.bind("<Return>", lambda _event: self.handle_text())

        send = tk.Button(controls, text="Send", command=self.handle_text, width=10)
        send.pack(side=tk.LEFT, padx=(8, 0), ipady=6)

        voice = tk.Button(controls, text="Voice", command=self.handle_voice, width=10)
        voice.pack(side=tk.LEFT, padx=(8, 0), ipady=6)

        self.write("Jarvis", startup_message())

    def write(self, speaker, text):
        self.output.insert(tk.END, f"{speaker}: {text}\n\n")
        self.output.see(tk.END)

    def handle_text(self):
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not command:
            return
        self.write("You", command)
        response = process_command(command)
        self.write("Jarvis", response)
        threading.Thread(target=speak, args=(response,), daemon=True).start()
        if response.startswith("Goodbye"):
            self.after(800, self.destroy)

    def handle_voice(self):
        def worker():
            command = obj.mic_input()
            if not command:
                self.write("Jarvis", "Voice input is not available or I could not hear a command.")
                return
            self.write("You", command)
            response = process_command(command)
            self.write("Jarvis", response)
            speak(response)

        threading.Thread(target=worker, daemon=True).start()


def run_cli():
    print(startup_message())
    while True:
        try:
            command = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        response = process_command(command)
        print(f"Jarvis: {response}")
        if response.startswith("Goodbye"):
            break


if __name__ == "__main__":
    if "--cli" in sys.argv or not os.environ.get("DISPLAY", "windows"):
        run_cli()
    else:
        JarvisApp().mainloop()
