import customtkinter as ctk
from nodebench.gui.i18n import t

class LogPanel(ctk.CTkFrame):
    MAX_LINES = 100

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._header = ctk.CTkLabel(self, text=t("log_title"), font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self._header.pack(fill="x", padx=6, pady=(2, 0))
        self._text = ctk.CTkTextbox(self, wrap="word", height=120, font=ctk.CTkFont(size=12))
        self._text.pack(fill="both", expand=True, padx=4, pady=2)
        self._text.configure(state="disabled")
        self._line_count = 0

    def set_title(self, title: str):
        self._header.configure(text=title)

    def write(self, message: str, color: str = "white"):
        self._text.configure(state="normal")
        tag = f"t{self._line_count}"
        self._text.insert("end", message + "\n")
        self._text.tag_add(tag, f"end-{len(message)+1}c", "end-1c")
        self._text.tag_config(tag, foreground=color)
        self._text.see("end")
        self._text.configure(state="disabled")
        self._line_count += 1
        if self._line_count > self.MAX_LINES:
            self._text.delete("1.0", "2.0")
            self._line_count -= 1

    def clear(self):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
        self._line_count = 0
