from tkinter import *


class GainMultiplier(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.combo = parent.combo
        self.wrapper = None
        self.btn = None
        self.grab_set()
        self.init_ui()

    def init_ui(self):

        self.wrapper = LabelFrame(self, text=self.combo.get())
        self.wrapper.pack(fill="both", expand=1, padx=10, pady=10)
        self.btn = Button(self, text='shoooo', width=10, command='')
        self.btn.config(state=NORMAL)
        self.btn.pack(side=RIGHT, padx=10, pady=10)
