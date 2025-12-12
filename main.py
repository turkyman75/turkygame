# main.py
# Turkygame - Sliding Number Puzzle (Kivy, English UI)

import random
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.animation import Animation
from kivy.core.window import Window


def hex_to_rgba(hex_color, alpha=1.0):
    """Convert HEX to RGBA for Kivy."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


class SplashScreen(Screen):
    """Simple splash screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = Label(
            text="[b]Turkygame[/b]",
            markup=True,
            font_size="40sp",
            halign="center",
            valign="middle",
        )
        subtitle = Label(
            text="Smart number puzzle",
            font_size="22sp",
            halign="center",
            valign="middle",
        )

        title.bind(size=self._update_label)
        subtitle.bind(size=self._update_label)

        layout.add_widget(title)
        layout.add_widget(subtitle)
        self.add_widget(layout)

    def _update_label(self, instance, *args):
        instance.text_size = instance.size

    def on_enter(self, *args):
        # Go to game screen after 2 seconds
        Clock.schedule_once(self.goto_game, 2)

    def goto_game(self, dt):
        self.manager.current = "game"


class GameScreen(Screen):
    """Main game screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Game settings
        self.size_n = 4          # 4×4 grid
        self.empty = 0
        self.board = []
        self.buttons = []

        self.total_time = 180    # 3 minutes
        self.remaining_time = self.total_time
        self.timer_event = None
        self.timer_running = False

        self.moves = 0

        # Row colors
        self.row_hex_colors = [
            "#ff9999",   # Row 1 - light red
            "#99ff99",   # Row 2 - light green
            "#99ccff",   # Row 3 - light blue
            "#fff799",   # Row 4 - light yellow
        ]
        self.row_colors = [hex_to_rgba(c) for c in self.row_hex_colors]
        self.empty_color = hex_to_rgba("#455a64")   # empty tile color
        self.bg_color = hex_to_rgba("#004d40")      # background color
        Window.clearcolor = self.bg_color

        # Optional move sound
        try:
            self.move_sound = SoundLoader.load("click.wav")
        except Exception:
            self.move_sound = None

        # Root layout
        root = BoxLayout(orientation="vertical", padding=10, spacing=8)
        self.add_widget(root)

        # Title
        title = Label(
            text="[b]Turkygame[/b]\nArrange numbers 1 to 15 before 3 minutes pass",
            markup=True,
            size_hint_y=None,
            height="90dp",
            font_size="20sp",
            halign="center",
            valign="middle",
        )
        title.bind(size=self._update_label)
        root.add_widget(title)

        # Info bar (moves + time)
        info_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="35dp",
            spacing=10,
        )

        self.moves_label = Label(
            text="Moves: 0",
            font_size="16sp",
            halign="left",
            valign="middle",
        )
        self.time_label = Label(
            text="Time left: 3:00",
            font_size="16sp",
            halign="right",
            valign="middle",
        )
        self.moves_label.bind(size=self._update_label)
        self.time_label.bind(size=self._update_label)
        info_bar.add_widget(self.moves_label)
        info_bar.add_widget(self.time_label)
        root.add_widget(info_bar)

        # Grid of tiles
        self.grid = GridLayout(
            cols=self.size_n,
            rows=self.size_n,
            spacing=5,
            size_hint_y=0.7,
        )
        root.add_widget(self.grid)

        # Bottom buttons
        bottom_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing=10,
        )

        new_game_btn = Button(
            text="New Game",
            font_size="16sp",
            on_press=self.on_new_game,
        )
        exit_btn = Button(
            text="Exit",
            font_size="16sp",
            on_press=self.on_exit,
        )

        for btn in (new_game_btn, exit_btn):
            btn.background_normal = ""
            btn.background_color = hex_to_rgba("#00796b")

        bottom_bar.add_widget(new_game_btn)
        bottom_bar.add_widget(exit_btn)
        root.add_widget(bottom_bar)

        # Build grid and start game
        self.create_buttons()
        self.start_new_game()

    def _update_label(self, instance, *args):
        instance.text_size = instance.size

    # --------- Create buttons ---------

    def create_buttons(self):
        self.grid.clear_widgets()
        self.buttons = []

        for r in range(self.size_n):
            row_btns = []
            for c in range(self.size_n):
                btn = Button(
                    text="",
                    font_size="26sp",
                    on_press=partial(self.on_tile_press, r, c),
                )
                btn.background_normal = ""
                btn.background_down = ""
                self.grid.add_widget(btn)
                row_btns.append(btn)
            self.buttons.append(row_btns)

    # --------- Start new game ---------

    def start_new_game(self, *args):
        # Ordered board
        numbers = list(range(1, self.size_n * self.size_n))
        numbers.append(self.empty)
        self.board = [
            numbers[i * self.size_n:(i + 1) * self.size_n]
            for i in range(self.size_n)
        ]

        # Reset counters
        self.moves = 0
        self.remaining_time = self.total_time
        self.moves_label.text = "Moves: 0"
        self.update_time_label()

        # Shuffle with random valid moves (always solvable)
        for _ in range(300):
            self.random_move()

        # Restart timer
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_running = True
        self.timer_event = Clock.schedule_interval(self.update_timer, 1.0)

        self.redraw_board()
        self.enable_all_buttons()

    def random_move(self):
        er, ec = self.find_empty()
        dirs = []
        if er > 0:
            dirs.append((er - 1, ec))
        if er < self.size_n - 1:
            dirs.append((er + 1, ec))
        if ec > 0:
            dirs.append((er, ec - 1))
        if ec < self.size_n - 1:
            dirs.append((er, ec + 1))

        if dirs:
            rr, cc = random.choice(dirs)
            self.board[er][ec], self.board[rr][cc] = self.board[rr][cc], self.board[er][ec]

    def find_empty(self):
        for r in range(self.size_n):
            for c in range(self.size_n):
                if self.board[r][c] == self.empty:
                    return r, c
        return None, None

    def redraw_board(self):
        for r in range(self.size_n):
            for c in range(self.size_n):
                val = self.board[r][c]
                btn = self.buttons[r][c]

                if val == self.empty:
                    btn.text = ""
                    btn.disabled = True
                    btn.background_color = self.empty_color
                else:
                    btn.text = str(val)
                    btn.disabled = False
                    btn.background_color = self.row_colors[r]

                btn.background_normal = ""
                btn.background_down = ""

    # --------- Timer ---------

    def update_time_label(self):
        m = self.remaining_time // 60
        s = self.remaining_time % 60
        self.time_label.text = f"Time left: {m}:{s:02d}"

    def update_timer(self, dt):
        if not self.timer_running:
            return

        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_time_label()
        else:
            self.timer_running = False
            self.update_time_label()
            self.disable_all_buttons()

            from kivy.uix.popup import Popup
            Popup(
                title="Time is up ⏰",
                content=Label(
                    text="You ran out of time before finishing the puzzle!",
                    font_size="16sp",
                ),
                size_hint=(0.7, 0.4),
            ).open()

            if self.timer_event:
                self.timer_event.cancel()

    # --------- Tile interaction ---------

    def on_tile_press(self, r, c, instance):
        if not self.timer_running or self.remaining_time <= 0:
            return

        val = self.board[r][c]
        if val == self.empty:
            return

        er, ec = self.find_empty()

        # Adjacent to empty?
        if (abs(er - r) == 1 and ec == c) or (abs(ec - c) == 1 and er == r):
            self.board[er][ec], self.board[r][c] = self.board[r][c], self.board[er][ec]
            self.moves += 1
            self.moves_label.text = f"Moves: {self.moves}"

            self.redraw_board()
            self.animate_button(er, ec)

            if self.move_sound:
                self.move_sound.play()

            self.check_win()

    def animate_button(self, r, c):
        """Simple flash animation."""
        btn = self.buttons[r][c]
        orig = btn.background_color[:]
        anim = (
            Animation(background_color=(1, 1, 1, 1), duration=0.08) +
            Animation(background_color=orig, duration=0.08)
        )
        anim.start(btn)

    # --------- Check win ---------

    def check_win(self):
        correct = list(range(1, self.size_n * self.size_n))
        correct.append(self.empty)

        flat = [self.board[r][c] for r in range(self.size_n) for c in range(self.size_n)]

        if flat == correct:
            self.timer_running = False
            if self.timer_event:
                self.timer_event.cancel()
            self.disable_all_buttons()

            elapsed = self.total_time - self.remaining_time
            m = elapsed // 60
            s = elapsed % 60

            from kivy.uix.popup import Popup
            Popup(
                title="Congratulations 🎉",
                content=Label(
                    text=f"Great job!\nMoves: {self.moves}\nTime: {m}:{s:02d}",
                    font_size="16sp",
                ),
                size_hint=(0.7, 0.4),
            ).open()

    # --------- Enable / disable buttons ---------

    def disable_all_buttons(self):
        for row in self.buttons:
            for btn in row:
                btn.disabled = True

    def enable_all_buttons(self):
        for r in range(self.size_n):
            for c in range(self.size_n):
                val = self.board[r][c]
                btn = self.buttons[r][c]

                if val == self.empty:
                    btn.disabled = True
                    btn.background_color = self.empty_color
                else:
                    btn.disabled = False
                    btn.background_color = self.row_colors[r]

                btn.background_normal = ""
                btn.background_down = ""

    # --------- Control buttons ---------

    def on_new_game(self, *args):
        self.start_new_game()

    def on_exit(self, *args):
        App.get_running_app().stop()


class TurkygameApp(App):
    title = "Turkygame - Number Puzzle"

    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.4))
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(GameScreen(name="game"))
        sm.current = "splash"
        return sm


if __name__ == "__main__":
    TurkygameApp().run()
