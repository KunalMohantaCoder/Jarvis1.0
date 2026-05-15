import requests

def tell_me_about(topic):
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(topic)
        response = requests.get(
            url,
            headers={"User-Agent": "JarvisAssistant/1.0 (local desktop assistant)"},
            timeout=10,
        )
        if response.status_code == 404:
            return False
        response.raise_for_status()
        data = response.json()
        return data.get("extract") or False
    except Exception as e:
        print(e)
        return False
