"""Графический интерфейс эмулятора на tkinter.

Окно похоже на терминал: сверху область вывода, снизу строка ввода
с приглашением. Стрелки вверх/вниз листают историю введённых команд.
"""

import tkinter as tk
from tkinter import scrolledtext

WINDOW_TITLE = "Shell Emulator"
WINDOW_SIZE = "800x500"
FONT = "TkFixedFont"
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
PROMPT_COLOR = "#6a9955"
ERROR_COLOR = "#f48771"
WELCOME = "Shell Emulator. Type 'exit' to quit.\n"


class TerminalWindow:
    """Окно терминала, связанное с сеансом оболочки Shell."""

    def __init__(self, shell, root=None):
        """Создать окно для сеанса shell (root — готовый tk.Tk)."""
        self.shell = shell
        self.exit_code = 0
        self.root = root if root is not None else tk.Tk()
        self.root.title(f"{WINDOW_TITLE} — {shell.vfs_name}")
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG_COLOR)
        self._history = []
        self._history_pos = 0
        self._build_output()
        self._build_input()
        self.write(WELCOME)

    def _build_output(self):
        """Создать область вывода только для чтения."""
        self.output = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word", font=FONT,
            bg=BG_COLOR, fg=FG_COLOR, borderwidth=0,
        )
        self.output.tag_configure("prompt", foreground=PROMPT_COLOR)
        self.output.tag_configure("error", foreground=ERROR_COLOR)
        self.output.pack(fill="both", expand=True)

    def _build_input(self):
        """Создать строку ввода с приглашением."""
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(fill="x")
        self.prompt_label = tk.Label(
            frame, text=self.shell.prompt, font=FONT,
            bg=BG_COLOR, fg=PROMPT_COLOR,
        )
        self.prompt_label.pack(side="left")
        self.entry = tk.Entry(
            frame, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            insertbackground=FG_COLOR, borderwidth=0,
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>", self._on_history_up)
        self.entry.bind("<Down>", self._on_history_down)
        self.entry.focus_set()

    def write(self, text, tag=()):
        """Добавить текст в область вывода (tag — стиль оформления)."""
        self.output.configure(state="normal")
        self.output.insert("end", text, tag)
        self.output.see("end")
        self.output.configure(state="disabled")

    def run_line(self, line):
        """Показать введённую строку, выполнить её и вывести результат."""
        self.write(self.shell.prompt, "prompt")
        self.write(line + "\n")
        result = self.shell.execute(line)
        if result.output:
            self.write(result.output + "\n")
        if result.error:
            self.write(result.error + "\n", "error")
        self.prompt_label.configure(text=self.shell.prompt)
        if result.should_exit:
            self.exit_code = result.exit_code
            self.root.destroy()
        return result

    def mainloop(self):
        """Запустить цикл обработки событий окна."""
        self.root.mainloop()

    def _on_enter(self, _event):
        """Обработать нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        if line.strip():
            self._history.append(line)
        self._history_pos = len(self._history)
        self.run_line(line)
        return "break"

    def _on_history_up(self, _event):
        """Показать предыдущую команду из истории."""
        if self._history_pos > 0:
            self._history_pos -= 1
            self._set_entry(self._history[self._history_pos])
        return "break"

    def _on_history_down(self, _event):
        """Показать следующую команду из истории."""
        self._history_pos = min(self._history_pos + 1, len(self._history))
        if self._history_pos < len(self._history):
            self._set_entry(self._history[self._history_pos])
        else:
            self._set_entry("")
        return "break"

    def _set_entry(self, text):
        """Заменить содержимое строки ввода."""
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
