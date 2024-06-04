from textual.app import App, ComposeResult
from textual.widgets import Header


class HeaderApp(App):
    def compose(self) -> ComposeResult:
        yield Header()


app = HeaderApp()
app.run()
