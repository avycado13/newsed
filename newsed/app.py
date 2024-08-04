import random
from datetime import datetime
import argparse
import importlib.util
import requests
from bs4 import BeautifulSoup
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
    if user_script and url in user_script.url_parsing_dict:
        return user_script.url_parsing_dict[url](soup, url)
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
        urls = list(user_script.url_parsing_dict.keys())
    else:
        urls = [
            "https://lite.cnn.com",
            "https://legiblenews.com",
            "https://text.npr.org",
        ]

    for url in urls:
        print(f"Articles from {term.link(url, url)}:")
        soup = BeautifulSoup(requests.get(url, timeout=10).content, "html.parser")
        textwrap_kwargs = {
            "width": term.width - (term.width // 4),
            "initial_indent": " " * (term.width // 6) + "* ",
            "subsequent_indent": (" " * (term.width // 6)) + " " * 2,
        }
        article_count = 0
        for a_href in find_articles(soup, url):
            if article_count >= args.a:
                break
            url_id = random.randrange(0, 1 << 24)
            for line in term.wrap(make_bold(term, a_href.text), **textwrap_kwargs):
                print(whitespace_only(term, line), end="")
                print(term.link(a_href.get("href"), line.lstrip(), url_id))
            article_count += 1

    print(f"\nWeather from {term.link('https://wttr.in', 'wttr.in')}:")
    weather_response = requests.get("http://wttr.in/?format=%C+%t+%w", timeout=10)
    print(weather_response.text)


if __name__ == "__main__":
    main()
