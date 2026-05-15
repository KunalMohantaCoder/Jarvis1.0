import requests

import config

try:
    from memory import USER_MEMORY
except Exception:
    USER_MEMORY = {}


class JarvisAI:
    def __init__(self):
        self.history = []

    def ask(self, prompt):
        provider = getattr(config, "ai_provider", "auto").lower()
        if provider == "groq" or (provider == "auto" and _configured("groq_api_key")):
            return self._ask_groq(prompt)
        if provider == "gemini" or (provider == "auto" and _configured("gemini_api_key")):
            return self._ask_gemini(prompt)
        return "AI assistant is ready, but it needs a Gemini or Groq API key in config.py."

    def _system_prompt(self):
        title = USER_MEMORY.get("preferred_title", "the user")
        exam_goal = USER_MEMORY.get("exam_goal", "his studies")
        return (
            "You are J.A.R.V.I.S, a calm, capable personal AI assistant. "
            f"You address the user as {title}. "
            f"The user is preparing for {exam_goal}, so help with study planning, explanations, "
            "problem solving, productivity, and computer assistance. "
            "Be direct, trustworthy, and concise. Avoid exaggerated sci-fi language."
        )

    def _messages(self, prompt):
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(self.history[-8:])
        messages.append({"role": "user", "content": prompt})
        return messages

    def _remember(self, prompt, answer):
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": answer})
        self.history = self.history[-10:]

    def _ask_groq(self, prompt):
        api_key = getattr(config, "groq_api_key", "")
        model = getattr(config, "groq_model", "llama-3.3-70b-versatile")
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": self._messages(prompt),
                    "temperature": 0.4,
                    "max_completion_tokens": 700,
                },
                timeout=45,
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"].strip()
            self._remember(prompt, answer)
            return answer
        except Exception as exc:
            return f"Groq AI request failed: {exc}"

    def _ask_gemini(self, prompt):
        api_key = getattr(config, "gemini_api_key", "")
        model = getattr(config, "gemini_model", "gemini-2.5-flash")
        contents = []
        for message in self.history[-8:]:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message["content"]}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json={
                    "system_instruction": {"parts": [{"text": self._system_prompt()}]},
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 700,
                    },
                },
                timeout=45,
            )
            response.raise_for_status()
            parts = response.json()["candidates"][0]["content"].get("parts", [])
            answer = "".join(part.get("text", "") for part in parts).strip()
            if not answer:
                return "Gemini returned an empty answer."
            self._remember(prompt, answer)
            return answer
        except Exception as exc:
            return f"Gemini AI request failed: {exc}"


def _configured(name):
    value = getattr(config, name, "")
    return bool(value and not str(value).startswith("<"))
