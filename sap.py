# importing ui components
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container
from textual.binding import Binding
from textual.widgets import (
    Header,
    ProgressBar,
    MarkdownViewer,
    Markdown,
    TabPane,
    TabbedContent,
    Button,
    Input,
    Label,
    ListView,
    ListItem,
)
from textual.containers import Container, Vertical, Horizontal, Center
from textual.command import Hit, Hits, Provider
from textual import work
from textual.reactive import reactive
from textual.message import Message

#backend
from json import load, dump

# importing stuff to play the music
from pygame import mixer

# miscellaneous imports (is tht the right spelling tho?)
from time import sleep
from os import listdir
from functools import partial
from pathlib import Path

volume = 1
q = []
p = []
is_paused = False
is_running = True
song = ""

mixer.init()

DOWNLOADS = """\
# Downloaded Songs

| No. | Name | Path |
|-----|------|------|
"""
songs = listdir("songs")

for no, song in enumerate(songs, start=1):
    if song != "◌󠇯.txt":
        DOWNLOADS += f"|{no}|{song}|{str(Path().absolute())+f'\\songs\\{song}.mp3'}|\n"

QUEUE = """
# Queued Songs

| No. | Name | Path |
|-----|------|------|
"""


PLAYLISTS = """
# Playlists

"""

help_text = """
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
| playlist queue {playlist_name} | Queues the playlist |
| switch {tab} | Switches to the mentioned tab |
| clear queue | Clears the queue |

## About
Check out the [GitHub](https://github.com/Avn3s/textsap) for more information.

Gimme a ⭐ if you like it plz uwuwu <3 (@_@)<-Cute pleading face.
Enjoy.
"""


ROWS = [
    ("No.", "Song"),
]
for no, song in enumerate(listdir("songs"), start=1):
    ROWS.append(tuple([no, song]))

def get_playlists():
    with open("playlists.json", "r") as file:
        playlists = load(file)
        return playlists

def format_playlists_for_display():
    playlists = get_playlists()
    formatted_playlists = "# Playlists\n\n"
    for playlist_name, songs in playlists.items():
        formatted_playlists += f"**{playlist_name}**\n\n"
        for song in songs:
            formatted_playlists += f"- {song[:-4]}\n"
        formatted_playlists += "\n"
    return formatted_playlists

class ReactiveMarkdown(Markdown):
    content = reactive("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_content()

    def update_content(self) -> None:
        self.update(self.content)

    def watch_content(self, new_content: str) -> None:
        self.update_content()


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
        help_score = matcher.match("help")
        if help_score > 0:
            yield Hit(
                help_score,
                matcher.highlight(query),
                partial(self.app.action_help),
                help="Shows help regarding commands and keybinds",
                text="Shows help regarding commands and keybinds",
            )
        pause_score = matcher.match("pause")
        if pause_score > 0:
            yield Hit(
                pause_score,
                matcher.highlight(query),
                partial(self.app.action_toggle_pause),
                help="Pauses the current song.",
                text="Pauses the current song.",
            )
        resume_score = matcher.match("resume")
        if resume_score > 0:
            yield Hit(
                resume_score,
                matcher.highlight(query),
                partial(self.app.action_toggle_pause),
                help="Resumes the current song.",
                text="Resumes the current song.",
            )
        for tab in ["Downloads", "Queue", "Playlists"]:
            score = matcher.match(f"switch {tab}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.action_switch_tab, tab),
                    help=f"Switches to the {tab} tab.",
                    text=f"Switches to the {tab} tab.",
                )
        playlists=get_playlists()
        for playlist in playlists:
            score=matcher.match(f"playlist queue {playlist}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(query),
                    partial(self.app.queue_playlist, playlist),
                    help=f"Queues all songs in the {playlist} playlist.",
                    text=f"Queues all songs in the {playlist} playlist.",
                )
        score=matcher.match("clear queue")
        if score>0:
            yield Hit(
                score,
                matcher.highlight(query),
                partial(self.app.action_clear_queue),
                help="Clears the queue.",
                text="Clears the queue.",
            )

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
        border: solid yellow;
    }
    
    """

    def compose(self) -> ComposeResult:
        global help_text
        with Container(id="help"):
            yield MarkdownViewer(markdown=help_text, show_table_of_contents=True)

class Sappy(App):
    global volume, q, p, is_paused, song, length
    App.COMMANDS = {songsProvider} | App.COMMANDS

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
        Binding(key="?", action="help", description="Help"),
        Binding(key="left", action="rewind", description="rewind"),
        Binding(key="right", action="forward", description="forward"),
    ]

    @work(exclusive=True, thread=True)
    async def songplay(self) -> None:
        global isPaused, q, is_running, p, song, QUEUE
        while True:
            if not mixer.music.get_busy() and not is_paused:
                if len(q) != 0:
                    try:
                        mixer.music.unload()
                        song = q.pop(0)
                        p.append(song)
                        mixer.music.load(song)
                        # mixer.music.set_volume(volume)
                        mixer.music.play()
                        self.notify(title="Now Playing", message=song[8:-4:])
                    except:
                        pass
            if not is_running:
                quit()
            sleep(2)

    _queue_content = reactive(QUEUE)
    _playlists_content = reactive(PLAYLISTS)

    @property
    def queue_content(self):
        return self._queue_content

    @queue_content.setter
    def queue_content(self, value):
        self._queue_content = value
        self.query_one("#queue_content", ReactiveMarkdown).content = value

    @property
    def playlists_content(self):
        return self._playlists_content

    @playlists_content.setter
    def playlists_content(self, value):
        self._playlists_content = value
        self.query_one("#playlists_content", ReactiveMarkdown).content = value

    def on_mount(self) -> None:
        self.query_one("#volume").advance(100)
        self.songplay()
        self.update_playlists_display()
    
    def action_quit(self) -> None:
        global is_running
        is_running = False
        exit()

    def update_playlists_display(self):
        playlists_content = format_playlists_for_display()
        self.query_one("#playlists_content", ReactiveMarkdown).content = playlists_content
    def play_song(self, song: str) -> None:
        q.clear()
        # mixer.music.set_volume(volume)
        mixer.music.unload()
        mixer.music.load("./songs/" + song)
        mixer.music.play()
        self.notify(title="Now Playing", message=song[:-4:])

    def queue_song(self, song: str) -> None:
        global q, QUEUE, volume
        # mixer.music.set_volume(volume)
        q.append("./songs/" + song)
        self.notify(title="Added to queue", message=song[:-4:], severity="warning")
        self.update_queue_display()

    def update_queue_display(self) -> None:
        global QUEUE, q
        QUEUE = "# Queued Songs\n\n| No. | Name | Path |\n|-----|------|------|\n"
        for index, song in enumerate(q, start=1):
            song_name = song.split('/')[-1][:-4]  # Remove path and file extension
            QUEUE += f"| {index} | {song_name} | {song} |\n"
        self.query_one("#queue_content", ReactiveMarkdown).content = QUEUE
    def action_increase_volume(self) -> None:
        self.query_one("#volume").advance(5)
        volume = mixer.music.get_volume()
        volume += 0.05
        mixer.music.set_volume(volume)
    
    def queue_playlist(self, playlist_name) -> None:
        global QUEUE, q
        playlists = get_playlists()
        
        for song in playlists[playlist_name]:
            q.append("./songs/" + song)
        
        QUEUE = "# Queued Songs\n\n| No. | Name | Path |\n|-----|------|------|\n"
        for index, song in enumerate(q, start=1):
            song_name = song.split('/')[-1][:-4]  # Remove path and file extension
            QUEUE += f"| {index} | {song_name} | {song} |\n"
        
        self.query_one("#queue_content", ReactiveMarkdown).content = QUEUE
        self.notify(title="Playlist added to queue", message=playlist_name, severity="warning")

    def action_decrease_volume(self) -> None:
        self.query_one("#volume").advance(-5)
        volume = mixer.music.get_volume()
        volume -= 0.05
        mixer.music.set_volume(volume)

    def action_switch_tab(self, tab: str) -> None:
        global QUEUE, q
        self.query_one(TabbedContent).active = tab.lower()
        for no, song in enumerate(q, start=1):
            QUEUE += f"|{no}|{song}|bob|\n"

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
        try:    
            q.insert(0, p.pop())
            q.insert(0, p.pop())
            mixer.music.stop()
            mixer.music.unload()
        except:
            self.notify(title="No previous songs", message="There are no previous songs in the queue", severity="error")
            
    def action_help(self) -> None:
        self.push_screen(HelpScreen())
    
    def action_clear_queue(self) -> None:
        global q, QUEUE
        q.clear()
        mixer.music.stop()
        mixer.music.unload()
        self.update_queue_display()
        self.notify(title="Queue Cleared", message="All songs have been removed from the queue", severity="information")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


    def compose(self) -> ComposeResult:
        with Vertical():
            self.title = "Sap.py"
            self.sub_title = "~Avn3s"
            yield Header(show_clock=True)
            with TabbedContent(initial="downloads"):
                with TabPane("Downloads", id="downloads"):
                    yield Markdown(DOWNLOADS)
                with TabPane("Queue", id="queue"):
                    yield ReactiveMarkdown(QUEUE, id="queue_content")
                with TabPane("Playlists", id="playlists"):
                    yield ReactiveMarkdown(PLAYLISTS, id="playlists_content")
            yield MarkdownViewer(
                DOWNLOADS, show_table_of_contents=False, classes="songlist"
            )
            with Center():
                yield ProgressBar(total=100, show_eta=False, id="volume")


app = Sappy()
app.run()
