import webbrowser

def website_opener(domain):
    try:
        if domain.startswith(("http://", "https://")):
            url = domain
        elif "." in domain:
            url = "https://" + domain
        else:
            url = "https://www." + domain + ".com"
        webbrowser.open(url)
        return url
    except Exception as e:
        print(e)
        return False
