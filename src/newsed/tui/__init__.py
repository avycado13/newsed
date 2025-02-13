from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.widgets import Markdown, OptionList
from textual.widgets.option_list import Option, Separator
import click
from markdownify import markdownify as md
import requests


class TUI(App[None]):
    def __init__(
        self,
        url: str = "https://example.com",
        urls: list[tuple[str, str]] = [("Example 1", "example.com")],
    ) -> None:
        self.url = url
        self.urls = urls
        self.url_marked_as_read: bool = False
        super().__init__()

    def fetch_news(self, url) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.log(f"Error fetching news from {url}: {e}")
            return "Error fetching news. Please try again later."

    """A Textual app to read the news."""
    CSS_PATH = "main.tcss"

    def _set_bindings(self):
        status = "unread" if self.url_marked_as_read else "read"
        BINDINGS = [
            ("d", "toggle_dark", "Toggle dark mode"),
            ("r", "mark_as_read", f"Mark as {status}"),
        ]
        return BINDINGS

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "mark_as_read", "Mark as read"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        self.rendered_content = md(self.fetch_news(self.url))
        yield Header(show_clock=True)
        yield (
            OptionList(
                Separator(),
                Option("Back", self.urls[1][1] if len(self.urls) > 1 else ""),
                Option("Next", self.urls[1][1] if len(self.urls) > 1 else ""),
                Separator(),
                *(Option(url[0], url[1]) for url in self.urls),
                id="sidebar",
            )
        )
        yield Markdown(self.rendered_content, id="body")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_mark_as_read(self) -> None:
        """An action to mark the current option as read."""
        for option in self.query_one("#sidebar", OptionList)._options:
            if option.id == self.url:
                option._prompt = f"[Read]{option.prompt}"
                break

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        selected_option = event.option
        self.url = selected_option.id
        self.rendered_content = md(self.fetch_news(self.url))
        self.query_one("#body", Markdown).update(self.rendered_content)


@click.group(invoke_without_command=True)
@click.option(
    "--source", type=str, help="Specify the url of the article.", multiple=True, nargs=4
)
@click.pass_context
def main(ctx: click.Context, source: tuple[str]) -> None:
    try:
        urls = [(f"Source {i + 1}", url) for i, url in enumerate(source)]
        app = TUI(urls=urls)
        app.run()
    except Exception as e:
        click.echo(f"An error occurred: {e}")
