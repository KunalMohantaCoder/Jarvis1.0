import datetime
import importlib

import pyttsx3

import date_time
import launch_app
import note
import send_email
import website_open


def _optional_module(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:
        print(f"{name} is unavailable: {exc}")
        return None


class JarvisAssistant:
    """Small facade around Jarvis features with graceful optional dependency handling."""

    def __init__(self):
        self._last_text_input = None
        self._engine = None

    def get_input(self, use_mic=False):
        if self._last_text_input:
            command = self._last_text_input
            self._last_text_input = None
            return command
        if use_mic:
            return self.mic_input()
        return input("Command: ").strip().lower()

    def mic_input(self):
        try:
            sr = importlib.import_module("speech_recognition")
        except Exception as exc:
            print(f"Voice input is unavailable: {exc}")
            return False

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.energy_threshold = 4000
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Recognizing...")
            command = recognizer.recognize_google(audio, language="en-in").lower()
            print(f"You said: {command}")
            return command
        except Exception as exc:
            print(f"Voice input failed: {exc}")
            return False

    def _get_engine(self):
        if self._engine is None:
            self._engine = pyttsx3.init("sapi5")
            voices = self._engine.getProperty("voices")
            if voices:
                self._engine.setProperty("voice", voices[0].id)
            self._engine.setProperty("rate", 175)
        return self._engine

    def tts(self, text):
        if not text:
            return False
        print(text)
        try:
            engine = self._get_engine()
            engine.say(str(text))
            engine.runAndWait()
            return True
        except Exception as exc:
            print(f"Text-to-speech is unavailable: {exc}")
            return False

    def tell_me_date(self):
        return date_time.date()

    def tell_time(self):
        return date_time.time()

    def launch_any_app(self, path_of_app):
        return launch_app.launch_app(path_of_app)

    def website_opener(self, domain):
        return website_open.website_opener(domain)

    def weather(self, city):
        weather_feature = _optional_module("weather")
        if not weather_feature:
            return "Weather is unavailable because its dependencies could not be loaded."
        return weather_feature.fetch_weather(city)

    def tell_me(self, topic):
        wikipedia_feature = _optional_module("wikipedia")
        if not wikipedia_feature:
            return "Wikipedia lookup is unavailable because the wikipedia package is not installed."
        return wikipedia_feature.tell_me_about(topic)

    def news(self):
        news = _optional_module("news")
        if not news:
            return False
        return news.get_news()

    def send_mail(self, sender_email, sender_password, receiver_email, msg):
        return send_email.mail(sender_email, sender_password, receiver_email, msg)

    def google_calendar_events(self, text):
        google_calendar = _optional_module("google_calendar")
        if not google_calendar:
            return "Google Calendar is unavailable because its dependencies could not be loaded."
        service = google_calendar.authenticate_google()
        event_date = google_calendar.get_date(text)
        if event_date:
            return google_calendar.get_events(event_date, service)
        return None

    def search_anything_google(self, command):
        google_search = _optional_module("google_search")
        if not google_search:
            return False
        return google_search.google_search(command)

    def take_note(self, text):
        return note.note(text)

    def system_info(self):
        system_stats = _optional_module("system_stats")
        if not system_stats:
            return "System stats are unavailable because psutil is not installed."
        return system_stats.system_stats()

    def location(self, location):
        loc = _optional_module("loc")
        if not loc:
            raise RuntimeError("Location dependencies could not be loaded.")
        current_loc, target_loc, distance = loc.loc(location)
        return current_loc, target_loc, distance

    def my_location(self):
        loc = _optional_module("loc")
        if not loc:
            raise RuntimeError("Location dependencies could not be loaded.")
        city, state, country = loc.my_location()
        return city, state, country

    def calculate_locally(self, expression):
        allowed = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow}
        try:
            return str(eval(expression, {"__builtins__": {}}, allowed))
        except Exception:
            return None

    def greeting(self):
        hour = datetime.datetime.now().hour
        if hour <= 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"
