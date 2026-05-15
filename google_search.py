import re
import urllib.parse
import webbrowser


def google_search(command):
    reg_ex = re.search('search google for (.*)', command)
    search_for = command.split("for", 1)[1] if "for" in command else command
    if reg_ex:
        search_for = reg_ex.group(1)
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(search_for.strip())
    webbrowser.open(url)
    return url
