import base64
import datetime
import importlib
import os
import subprocess
import tempfile
import wave
import winsound

import requests

import date_time
import launch_app
import note
import send_email
import website_open
import config


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
        sarvam_command = self._sarvam_mic_input()
        if sarvam_command:
            return sarvam_command

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
        except AttributeError as exc:
            if "PyAudio" in str(exc):
                print("Voice input needs PyAudio. Install Microsoft C++ Build Tools or use Python 3.11 with a PyAudio wheel.")
            else:
                print(f"Voice input failed: {exc}")
            return False
        except Exception as exc:
            print(f"Voice input failed: {exc}")
            return False

    def _sarvam_mic_input(self, seconds=5, sample_rate=16000):
        api_key = getattr(config, "sarvam_api_key", "")
        if not api_key or api_key.startswith("<"):
            return False

        audio_path = None
        try:
            import sounddevice as sd

            print(f"Listening for {seconds} seconds...")
            recording = sd.rec(
                int(seconds * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_path = audio_file.name

            with wave.open(audio_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(recording.tobytes())

            print("Transcribing with Sarvam...")
            with open(audio_path, "rb") as audio_file:
                response = requests.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers={"api-subscription-key": api_key},
                    files={"file": ("command.wav", audio_file, "audio/wav")},
                    timeout=45,
                )
            response.raise_for_status()
            transcript = (response.json().get("transcript") or "").strip().lower()
            if transcript:
                print(f"You said: {transcript}")
                return transcript
            print("Sarvam did not return a transcript.")
            return False
        except Exception as exc:
            print(f"Sarvam voice input failed: {exc}")
            return False
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

    def _get_engine(self):
        if self._engine is None:
            pyttsx3 = importlib.import_module("pyttsx3")
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
        if self._sarvam_tts(str(text)):
            return True
        try:
            engine = self._get_engine()
            engine.say(str(text))
            engine.runAndWait()
            return True
        except Exception as exc:
            return self._windows_tts(str(text), exc)

    def _windows_tts(self, text, original_error):
        script_text = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$speaker.Rate = 0; "
            f"$speaker.Speak('{script_text}')"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return True
        except Exception as fallback_error:
            print(f"Text-to-speech is unavailable: {original_error}; fallback failed: {fallback_error}")
            return False

    def _sarvam_tts(self, text):
        api_key = getattr(config, "sarvam_api_key", "")
        if not api_key or api_key.startswith("<"):
            return False

        payload = {
            "text": text[:2500],
            "target_language_code": getattr(config, "sarvam_language_code", "en-IN"),
            "model": "bulbul:v3",
            "speaker": getattr(config, "sarvam_speaker", "shubh"),
            "pace": 1.0,
            "speech_sample_rate": 24000,
            "output_audio_codec": "wav",
        }
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }

        audio_path = None
        try:
            response = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            audios = data.get("audios") or []
            if not audios:
                return False

            audio_bytes = base64.b64decode(audios[0])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_file.write(audio_bytes)
                audio_path = audio_file.name

            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            return True
        except Exception as exc:
            print(f"Sarvam text-to-speech is unavailable: {exc}")
            return False
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

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
