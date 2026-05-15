import webbrowser, re
import urllib.parse
import urllib.request

def play_on_youtube(query):
    song = urllib.parse.urlencode({"search_query": query})
    result = urllib.request.urlopen("http://www.youtube.com/results?" + song)
    search_results = re.findall(r'href=\"\/watch\?v=(.{11})', result.read().decode())
    if not search_results:
        return False
    url = "http://www.youtube.com/watch?v=" + search_results[0]
    webbrowser.open_new(url)
    return url

if __name__ == "__main__":
    domain = input("Enter the song name: ")
    play_on_youtube(domain)
