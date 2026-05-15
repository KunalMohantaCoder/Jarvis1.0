import xml.etree.ElementTree as ET

import requests



def get_news():
    try:
        response = requests.get(getNewsUrl(), timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        articles = []
        for item in root.findall("./channel/item")[:10]:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            if title:
                articles.append({"title": title, "url": link})
        return articles
    except Exception as exc:
        print(exc)
        return False


def getNewsUrl():
    return 'https://timesofindia.indiatimes.com/rssfeedstopstories.cms'
