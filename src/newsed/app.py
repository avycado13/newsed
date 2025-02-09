from datetime import datetime
import importlib.util
import requests
from bs4 import BeautifulSoup
import feedparser
from rich.console import Console
from rich.text import Text
import click
from .processors import npr_processor, generic_processor

def load_user_script(script_path):
    spec = importlib.util.spec_from_file_location("user_script", script_path)
    user_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_script)
    return user_script

def embolden(phrase):
    return phrase.isdigit() or phrase[:1].isupper()

def make_bold(text):
    words = text.split(" ")
    return Text(" ").join(
        Text(word, style="bold") if embolden(word) else Text(word) for word in words
    )

def find_articles(soup, url, user_script):
    if user_script and url in user_script.urls:
        return user_script.urls[url](soup, url)
    elif "text.npr.org" in url:
        return npr_processor(soup)
    else:
        return generic_processor(soup)

@click.command()
@click.option('-a', default=5, help='Number of articles to print from each source.')
@click.option('-s', '--script', type=click.Path(exists=True), help='Path to the user-defined script file.')
@click.option('-u', '--url', type=str, help='Read a custom URL')
def main(a, script, url):
    console = Console()
    console.print(f"Current date and time: {datetime.now()}\n", style="bold")

    user_script = load_user_script(script) if script else None

    urls = [url] if url else (list(user_script.urls.keys()) if user_script else [
        "https://lite.cnn.com",
        "https://legiblenews.com",
        "https://text.npr.org",
    ])

    for url in urls:
        console.print(f"Articles from [link={url}]{url}[/link]:", style="bold")
        
        feed = feedparser.parse(url)
        if feed.bozo == 1:  # Not a valid RSS feed, fall back to scraping
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                
                article_count = 0
                for a_href in find_articles(soup, url, user_script):
                    if article_count >= a:
                        break
                    console.print(f"[link={url + a_href.get('href')}]{make_bold(a_href.text)}[/link]")
                    article_count += 1
            except requests.RequestException as e:
                console.print(f"Error fetching articles from {url}: {e}", style="bold red")
        else:
            article_count = 0
            for entry in feed.entries:
                if article_count >= a:
                    break
                console.print(make_bold(entry.title))
                console.print(f"[link={entry.link}]Read more[/link]")
                article_count += 1
        console.print("\n\n")

    console.print("\nWeather from [link=https://wttr.in]wttr.in[/link]:", style="bold")
    try:
        weather_response = requests.get("http://wttr.in/?format=%C+%t+%w", timeout=10)
        weather_response.raise_for_status()
        console.print(weather_response.text)
    except requests.RequestException as e:
        console.print(f"Error fetching weather: {e}", style="bold red")

if __name__ == "__main__":
    main()
