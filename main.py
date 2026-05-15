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
    THEMES = {
        "dark": {
            "bg": "#0f1115",
            "panel": "#171a21",
            "panel_2": "#1f232b",
            "text": "#f5f6f8",
            "muted": "#a5adba",
            "border": "#2d333d",
            "accent": "#3b82f6",
            "accent_text": "#ffffff",
            "input": "#11141a",
            "user": "#263348",
            "assistant": "#1d222b",
        },
        "light": {
            "bg": "#f6f7f9",
            "panel": "#ffffff",
            "panel_2": "#eef1f5",
            "text": "#1f2328",
            "muted": "#656d76",
            "border": "#d8dee4",
            "accent": "#2563eb",
            "accent_text": "#ffffff",
            "input": "#ffffff",
            "user": "#e8f0ff",
            "assistant": "#f3f4f6",
        },
    }

    def __init__(self):
        super().__init__()
        self.title("JARVIS")
        self.geometry("1040x700")
        self.minsize(860, 560)
        self.theme_name = "dark"
        self.widgets_to_theme = []
        self.shortcut_buttons = []

        self._build_ui()
        self.apply_theme()
        self.entry.bind("<Return>", lambda _event: self.handle_text())
        self.write("Jarvis", startup_message())

    def _build_ui(self):
        self.configure(bg=self.THEMES[self.theme_name]["bg"])
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.header = tk.Frame(self, height=64, bd=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)

        title_block = tk.Frame(self.header)
        title_block.grid(row=0, column=0, sticky="w", padx=22, pady=10)
        self.app_title = tk.Label(title_block, text="Jarvis", font=("Segoe UI", 17, "bold"), anchor="w")
        self.app_title.pack(anchor="w")
        self.app_subtitle = tk.Label(
            title_block,
            text="Personal assistant workspace",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.app_subtitle.pack(anchor="w")

        self.theme_button = tk.Button(
            self.header,
            text="Light mode",
            command=self.toggle_theme,
            width=12,
            cursor="hand2",
        )
        self.theme_button.grid(row=0, column=2, padx=(8, 22), pady=14, sticky="e")

        self.sidebar = tk.Frame(self, width=240, bd=0)
        self.sidebar.grid(row=1, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        self.nav_label = tk.Label(
            self.sidebar,
            text="Quick commands",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.nav_label.pack(fill=tk.X, padx=18, pady=(20, 10))

        shortcuts = [
            ("Time", "time"),
            ("Date", "date"),
            ("System status", "system"),
            ("Headlines", "news"),
            ("Search Google", "search google for "),
            ("Open website", "open "),
            ("Weather", "weather "),
            ("Note", "make a note "),
        ]
        for label, command in shortcuts:
            button = tk.Button(
                self.sidebar,
                text=label,
                anchor="w",
                command=lambda value=command: self.insert_shortcut(value),
                cursor="hand2",
            )
            button.pack(fill=tk.X, padx=14, pady=3, ipady=7)
            self.shortcut_buttons.append(button)

        self.sidebar_note = tk.Label(
            self.sidebar,
            text="Add API keys in config.py to enable weather, email, and WolframAlpha.",
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=190,
            anchor="w",
        )
        self.sidebar_note.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=18)

        self.content = tk.Frame(self, bd=0)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        self.content_header = tk.Frame(self.content)
        self.content_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        self.content_header.columnconfigure(0, weight=1)

        self.chat_title = tk.Label(
            self.content_header,
            text="Assistant",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        self.chat_title.grid(row=0, column=0, sticky="w")
        self.status_label = tk.Label(
            self.content_header,
            text="Ready",
            font=("Segoe UI", 9),
            anchor="e",
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        self.output = scrolledtext.ScrolledText(
            self.content,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=18,
            pady=16,
            bd=0,
        )
        self.output.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.output.configure(state=tk.DISABLED)

        self.composer = tk.Frame(self.content, bd=0)
        self.composer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.composer.columnconfigure(0, weight=1)

        self.entry = tk.Entry(
            self.composer,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            bd=0,
        )
        self.entry.grid(row=0, column=0, sticky="ew", ipady=12, padx=(12, 8), pady=10)

        self.voice_button = tk.Button(
            self.composer,
            text="Voice",
            command=self.handle_voice,
            width=9,
            cursor="hand2",
        )
        self.voice_button.grid(row=0, column=1, padx=(0, 8), pady=10, ipady=7)

        self.send_button = tk.Button(
            self.composer,
            text="Send",
            command=self.handle_text,
            width=9,
            cursor="hand2",
        )
        self.send_button.grid(row=0, column=2, padx=(0, 12), pady=10, ipady=7)

    def apply_theme(self):
        theme = self.THEMES[self.theme_name]
        self.configure(bg=theme["bg"])
        for widget in (self.header, self.sidebar, self.content, self.content_header):
            widget.configure(bg=theme["panel"])
        self.composer.configure(bg=theme["panel_2"], highlightthickness=1, highlightbackground=theme["border"])

        labels = [
            self.app_title,
            self.nav_label,
            self.chat_title,
        ]
        for label in labels:
            label.configure(bg=theme["panel"], fg=theme["text"])

        for label in (self.app_subtitle, self.sidebar_note, self.status_label):
            label.configure(bg=theme["panel"], fg=theme["muted"])

        self.output.configure(
            bg=theme["panel"],
            fg=theme["text"],
            insertbackground=theme["text"],
            highlightthickness=1,
            highlightbackground=theme["border"],
            selectbackground=theme["accent"],
        )
        self.output.tag_configure("speaker", foreground=theme["muted"], font=("Segoe UI", 9, "bold"))
        self.output.tag_configure("user", background=theme["user"], foreground=theme["text"], lmargin1=12, lmargin2=12, rmargin=12, spacing1=4, spacing3=12)
        self.output.tag_configure("assistant", background=theme["assistant"], foreground=theme["text"], lmargin1=12, lmargin2=12, rmargin=12, spacing1=4, spacing3=12)

        self.entry.configure(
            bg=theme["input"],
            fg=theme["text"],
            insertbackground=theme["text"],
            highlightthickness=1,
            highlightbackground=theme["border"],
        )

        primary_buttons = [self.send_button]
        secondary_buttons = [self.voice_button, self.theme_button, *self.shortcut_buttons]
        for button in primary_buttons:
            button.configure(
                bg=theme["accent"],
                fg=theme["accent_text"],
                activebackground=theme["accent"],
                activeforeground=theme["accent_text"],
                relief=tk.FLAT,
                bd=0,
                font=("Segoe UI", 10, "bold"),
            )
        for button in secondary_buttons:
            button.configure(
                bg=theme["panel_2"],
                fg=theme["text"],
                activebackground=theme["border"],
                activeforeground=theme["text"],
                relief=tk.FLAT,
                bd=0,
                font=("Segoe UI", 10),
            )

        self.theme_button.configure(text="Light mode" if self.theme_name == "dark" else "Dark mode")

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme()

    def insert_shortcut(self, command):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, command)
        self.entry.focus_set()
        if not command.endswith(" "):
            self.handle_text()

    def write(self, speaker, text):
        tag = "user" if speaker == "You" else "assistant"
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, f"{speaker}\n", ("speaker",))
        self.output.insert(tk.END, f"{text}\n\n", (tag,))
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def handle_text(self):
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not command:
            return
        self.write("You", command)
        self.status_label.configure(text="Processing")
        response = process_command(command)
        self.write("Jarvis", response)
        self.status_label.configure(text="Ready")
        threading.Thread(target=speak, args=(response,), daemon=True).start()
        if response.startswith("Goodbye"):
            self.after(800, self.destroy)

    def handle_voice(self):
        def worker():
            self.status_label.configure(text="Listening")
            command = obj.mic_input()
            if not command:
                self.write("Jarvis", "Voice input is not available or I could not hear a command.")
                self.status_label.configure(text="Ready")
                return
            self.write("You", command)
            self.status_label.configure(text="Processing")
            response = process_command(command)
            self.write("Jarvis", response)
            self.status_label.configure(text="Ready")
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
