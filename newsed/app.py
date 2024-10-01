import random
from datetime import datetime
import argparse
import importlib.util
import requests
from bs4 import BeautifulSoup
import feedparser
from blessed import Terminal

# Argument parser setup
parser = argparse.ArgumentParser(description="Print articles from various sources.")
parser.add_argument(
    "-a", type=int, default=5, help="Number of articles to print from each source."
)
parser.add_argument(
    "-s", "--script", type=str, help="Path to the user-defined script file."
)
parser.add_argument("-u", "--url", type=str, help="Read a custom URL")
args = parser.parse_args()

# Load user-defined script
def load_user_script(script_path):
    spec = importlib.util.spec_from_file_location("user_script", script_path)
    user_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_script)
    return user_script

user_script = load_user_script(args.script) if args.script else None

# Embolden phrases
def embolden(phrase):
    return phrase.isdigit() or phrase[:1].isupper()

def make_bold(term, text):
    return " ".join(
        term.bold(phrase) if embolden(phrase) else phrase for phrase in text.split(" ")
    )

def whitespace_only(term, line):
    return line[: term.length(line) - term.length(line.lstrip())]

def find_articles(soup, url):
    if user_script and url in user_script.urls:
        return user_script.urls[url](soup, url)
    elif "text.npr.org" in url:
        return (
            a_link
            for section in soup.find_all("div", class_="topic-container")
            for a_link in section.find_all("a")
        )
    else:
        return (
            a_link
            for section in soup.find_all("section")
            for a_link in section.find_all("a")
        )

def main():
    term = Terminal()
    print(f"Current date and time: {datetime.now()}\n")

    if args.url:
        urls = [args.url]
    elif user_script:
        urls = list(user_script.urls.keys())
    else:
        urls = [
            "https://lite.cnn.com",
            "https://legiblenews.com",
            "https://text.npr.org",
        ]

    for url in urls:
        textwrap_kwargs = {
            "width": term.width - (term.width // 4),
            "initial_indent": " " * (term.width // 6) + "* ",
            "subsequent_indent": " " * (term.width // 6) + " " * 2,
        }
        print(f"Articles from {term.link(url, url)}:")
        
        if feedparser.parse(url).bozo == 1:
            try:
                soup = BeautifulSoup(requests.get(url, timeout=10).content, "html.parser")
                article_count = 0
                for a_href in find_articles(soup, url):
                    if article_count >= args.a:
                        break
                    url_id = random.randrange(0, 1 << 24)
                    for line in term.wrap(make_bold(term, a_href.text), **textwrap_kwargs):
                        print(whitespace_only(term, line), end="")
                        print(term.link(a_href.get("href"), line.lstrip(), url_id))
                    article_count += 1
            except Exception as e:
                print(f"Error fetching articles from {url}: {e}")
        else:
            feed = feedparser.parse(url)
            article_count = 0
            for entry in feed.entries:
                if article_count >= args.a:
                    break
                url_id = random.randrange(0, 1 << 24)
                for line in term.wrap(make_bold(term, entry.title), **textwrap_kwargs):
                    print(whitespace_only(term, line), end="")
                    print(term.link(entry.link, line.lstrip(), url_id))
                article_count += 1

    print(f"\nWeather from {term.link('https://wttr.in', 'wttr.in')}:")
    try:
        weather_response = requests.get("http://wttr.in/?format=%C+%t+%w", timeout=10)
        print(weather_response.text)
    except Exception as e:
        print(f"Error fetching weather: {e}")

if __name__ == "__main__":
    main()
