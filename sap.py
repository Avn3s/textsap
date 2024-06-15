# importing ui
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, Input, DataTable
from textual.containers import ScrollableContainer, VerticalScroll
from textual.command import Hit, Hits, Provider
from textual import work

# importing stuff to play the music
from pygame import mixer

# miscellaneous imports (is tht the right spelling tho?)
from time import sleep
from os import listdir
from threading import Thread
from functools import partial
from keyboard import wait

volume = 1
q = []
p = []
isPaused=False
is_running=True

mixer.init()

ROWS = [
    ("No.", "Song"),
]
for no, song in enumerate(listdir("songs"), start=1):
    ROWS.append(tuple([no, song]))

"""def songplay():
    global isPaused, v, q, is_running, p
    while True:
        if mixer.music.get_busy() == False and isPaused == False:
            if len(q) != 0:
                mixer.music.unload()
                x = q.pop(0)
                p.append(x)
                mixer.music.load(x)
                mixer.music.set_volume(v)
                mixer.music.play()
        if is_running == False:
            quit()
        sleep(2)

songthread = Thread(target=songplay, args=())
"""

class songsProvider(Provider):
    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)

        for song in listdir("songs")[:-1:]:
            score = matcher.match(f"play {song}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.play_song, song),
                    help=f"Plays {song[:-3:]}",
                    text="play {song}",
                )
        
        for song in listdir("songs")[:-1:]:
            score=matcher.match(f"queue {song}")
            if score>0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.queue_song,song),
                    help=f"Queues {song[:-3:]}",
                    text="queue {song}"
                )

class Sappy(App):
    global volume, q, p
    COMMANDS = {songsProvider} | App.COMMANDS

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="d", action="toggle_dark", description="Toggle Dark mode"),
        Binding(key="down", action="decrease_volume", description="Decrease volume"),
        Binding(key="up", action="increase_volume", description="Increase volume"),
        Binding(key="↑".lower(), action="increase_volume", description="Increase volume"),
        Binding(key="↓".lower(), action="decrease_volume", description="Decrease volume"),
    ]
    @work(exclusive=True, thread=True)
    async def songplay(self)->None:
        global isPaused, volume, q, is_running, p
        while True:
            if mixer.music.get_busy() == False and isPaused == False:
                if len(q) != 0:
                    mixer.music.unload()
                    x = q.pop(0)
                    p.append(x)
                    mixer.music.load(x)
                    mixer.music.set_volume(volume)
                    mixer.music.play()
            if is_running == False:
                quit()
            sleep(2)

    #songthread = Thread(target=songplay, args=())

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
        self.songplay()

    def play_song(self, song: str) -> None:
        q.clear()
        mixer.music.set_volume(volume)
        mixer.music.unload()
        mixer.music.load("./songs/" + song)
        mixer.music.play()
    
    def queue_song(self, song:str)->None:
        mixer.music.set_volume(volume)
        q.append("./songs/"+song)

    def action_increase_volume(self) -> None:
        volume = mixer.music.get_volume()
        volume += 0.05
        mixer.music.set_volume(volume)

    def action_decrease_volume(self) -> None:
        volume = mixer.music.get_volume()
        volume -= 0.05
        mixer.music.set_volume(volume)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def compose(self) -> ComposeResult:
        self.title = "Sap.py"
        self.sub_title = "~Avn3s"
        yield Static("sidebar", id="sidebar")
        yield Header(
            show_clock=True,
        )
        yield Footer()
        yield DataTable(show_cursor=False)


app = Sappy()
app.run()
