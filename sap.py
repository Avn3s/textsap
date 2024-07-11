# importing ui
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import ScrollableContainer
from textual.binding import Binding
from textual.widgets import (
    Header,
    Footer,
    Static,
    Label,
    DataTable,
    ProgressBar,
    Button,
    MarkdownViewer,
    Markdown
)
from textual.containers import Container, Vertical, Horizontal, Center
from textual.command import Hit, Hits, Provider
from textual import work
from mutagen.mp3 import MP3

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
is_paused = False
is_running = True
is_change = False
song = ""

mixer.init()
song_list="""\
## Installed Songs

| No. | Name | Path |
|-----|------|------|
"""
songs=listdir("songs")

for no, song in enumerate(songs, start=1):
    if song!="◌󠇯.txt":
        song_list+=f"|{no}|{song}|bob|\n"

help_text="""

# Help Screen

## Keybinds
| Keybind | Description |
|---------|-------------|
| Ctrl+\ | Open the command prompt |
| Q | Quit the app |
| D | Toggle Dark / Light mode |
| ↑ | Increase Volume |
| ↓ | Decrease Volume |
| ← | Rewind by 10 seconds |
| → | Fast forward by 10 seconds |
| > | Skip the current song and play the next song in the queue |
| < | Play the previous song in the queue |
| esc |Close this help screen |

## Commands
| Command | Description |
|---------|-------------|
| queue {song} | Adds {song} to the queue |
| play {song} | Plays {song}, but removes items in the queue, if any |
| pause | Pauses the current song |
| resume | Resumes the current song |
| help | Opens this help screen|

Check out the [GitHub](https://github.com/Avn3s/textsap) for more information.

Gimme a ⭐ if you like it plz uwuwu <3 (@_@)<-Cute pleading face.
Enjoy.
"""



ROWS = [
    ("No.", "Song"),
]
for no, song in enumerate(listdir("songs"), start=1):
    ROWS.append(tuple([no, song]))


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
            score = matcher.match(f"queue {song}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.queue_song, song),
                    help=f"Queues {song[:-3:]}",
                    text="queue {song}",
                )
        help_score=matcher.match("help")
        if help_score>0:
            yield Hit(
                help_score,
                matcher.highlight(query),
                partial(self.app.action_help),
                help="Shows help regarding commands and keybinds",
                text="Shows help regarding commands and keybinds",
            )
        pause_score=matcher.match("pause")
        if pause_score>0:
            yield Hit(
                pause_score,
                matcher.highlight(query),
                partial(self.app.action_toggle_pause),
                help="Pauses the current song.",
                text="Pauses the current song.",
            )
        resume_score=matcher.match("resume")
        if resume_score>0:
            yield Hit(
                resume_score,
                matcher.highlight(query),
                partial(self.app.action_toggle_pause),
                help="Resumes the current song.",
                text="Resumes the current song.",
            )

class Volumebar(Static):
    DEFAULT_CSS="""
    
    Volumebar {
        width: 30%;
        height: 10%;
        background: $panel;
        padding: 1 1;
        align: center bottom;
    }
    
    """
    
    def compose(self)->ComposeResult:
        yield ProgressBar(total=100, id="volume_bar",)
        self.query_one(ProgressBar).value=100
    
    def key_up(self):
        self.query_one(ProgressBar).advance(5)
    
    def key_down(self):
        self.query_one(ProgressBar).advance(-5)
        

class HelpScreen(ModalScreen[None]):
    BINDINGS = [Binding(key="escape", action="pop_screen")]

    DEFAULT_CSS = """
    HelpScreen{
        align: center middle;

    }
    #help{
        width: auto;
        max-width: 70%;
        height: auto;
        max-height: 80%;
        background: $panel;
        align: center middle;
        padding: 2 4;
        border: solid green;
    }
    
    """

    def compose(self) -> ComposeResult:
        global help_text
        with Container(id="help"):
            yield MarkdownViewer(markdown=help_text, show_table_of_contents=True)   

class Sappy(App):
    global volume, q, p, is_paused, song, length
    COMMANDS = {songsProvider} | App.COMMANDS

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="d", action="toggle_dark", description="Toggle Dark mode"),
        Binding(key="down", action="decrease_volume", description="Decrease volume"),
        Binding(key="up", action="increase_volume", description="Increase volume"),
        Binding(
            key="↑".lower(), action="increase_volume", description="Increase volume"
        ),
        Binding(
            key="↓".lower(), action="decrease_volume", description="Decrease volume"
        ),
        Binding(key="space", action="toggle_pause", description="Pause/Resume"),
        Binding(key=">", action="next", description="Next song"),
        Binding(key="<", action="prev", description="Previous song"),
        Binding(key="h", action="help", description="Help"),
        Binding(key="left", action="rewind", description="rewind"),
        Binding(key="right", action="forward", description="forward"),
    ]

    @work(exclusive=True, thread=True)
    async def songplay(self) -> None:
        global isPaused, volume, q, is_running, p, song
        while True:
            if not mixer.music.get_busy() and not is_paused:
                if len(q) != 0:
                    mixer.music.unload()
                    song = q.pop(0)
                    p.append(song)
                    mixer.music.load(song)
                    mixer.music.set_volume(volume)
                    mixer.music.play()
                    self.notify(title="Now Playing", message=song[8:-4:])
            if not is_running:
                quit()
            sleep(2)
        
    
    def on_mount(self) -> None:
        self.songplay()

    def play_song(self, song: str) -> None:
        q.clear()
        mixer.music.set_volume(volume)
        mixer.music.unload()
        mixer.music.load("./songs/" + song)
        mixer.music.play()
        self.notify(title="Now Playing", message=song[:-4:])

    def queue_song(self, song: str) -> None:
        mixer.music.set_volume(volume)
        q.append("./songs/" + song)
        self.notify(title="Added to queue", message=song[:-4:], severity="warning")

    def action_increase_volume(self) -> None:
        volume = mixer.music.get_volume()
        volume += 0.05
        mixer.music.set_volume(volume)

    def action_decrease_volume(self) -> None:
        global volume
        volume = mixer.music.get_volume()
        volume -= 0.05
        mixer.music.set_volume(volume)

    def action_toggle_pause(self) -> None:
        global is_paused
        if is_paused:
            mixer.music.unpause()
        else:
            mixer.music.pause()
        is_paused = not is_paused

    def action_rewind(self) -> None:
        position = mixer.music.get_pos()
        mixer.music.set_pos((position - 5000) / 1000)
        del position

    def action_forward(self) -> None:
        position = mixer.music.get_pos()
        mixer.music.set_pos((position + 5000) / 1000)
        del position

    def action_next(self) -> None:
        mixer.music.stop()
        mixer.music.unload()

    def action_prev(self) -> None:
        global q, p
        q.insert(0, p.pop())
        q.insert(0, p.pop())
        mixer.music.stop()
        mixer.music.unload()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                self.title = "Sap.py"
                self.sub_title = "~Avn3s"
                yield Header(show_clock=True,)
                yield MarkdownViewer(song_list, show_table_of_contents=False, classes='songlist')
                with Center():
                    yield Volumebar()
app = Sappy()
app.run()
