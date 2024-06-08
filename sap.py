#importing ui
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header,Footer,Static,Input,DataTable
from textual.containers import ScrollableContainer,VerticalScroll
from textual.command import Hit, Hits, Provider

#importing stuff to play the music
from pygame import mixer

#miscellaneous imports (is tht the right spelling tho?)
from time import sleep
from os import listdir
from threading import Thread
from functools import partial

mixer.init()

ROWS=[
    ("No.","Song"),
    ]
for no,song in enumerate(listdir('songs'), start=1):
    ROWS.append(tuple([no,song]))

class songsProvider(Provider):
    async def search(self, query:str)->Hits:
        matcher=self.matcher(query)
        
        for song in listdir("songs")[:-1:]:
            score=matcher.match(song)
            if score>0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.play_song, song),
                    help=f"Plays {song[:-3:]}"
                    
                )

class Sappy(App):
    COMMANDS={songsProvider}
    
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="d", action="toggle_dark", description="Toggle Dark mode")
    ]
    
    def on_mount(self)->None:
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
    
    def play_song(self, song: str)->None:
        mixer.music.unload()
        mixer.music.load("./songs/"+song) 
        mixer.music.play()
    
    def set_volume(self, volume: float)->None:

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
    
    def compose(self) -> ComposeResult:
        self.title="Sap.py"
        self.sub_title="~Avn3s"
        yield Static("sidebar",id="sidebar")
        yield Header(show_clock=True,)
        yield Footer()
        yield DataTable(show_cursor=False)

app = Sappy()
app.run()