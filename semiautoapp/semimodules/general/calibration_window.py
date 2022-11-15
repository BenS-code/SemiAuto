from semiautoapp.semimodules.calibration_processes import *
from tkinter import messagebox
import threading


class CalibrationWin(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.parent.attributes('-disabled', 1)
        self.dir = parent.directory_entry.get()
        self.tv = parent.tv
        self.combo = parent.combo
        self.directory_entry = parent.directory_entry
        # self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.init_ui()

    def init_ui(self):
        self.title(self.combo.get())
        self.geometry('1250x400')
        self.minsize(1250, 400)
        self.resizable(width=True, height=True)

        if not self.tv.get_children():
            self.destroy()
            messagebox.showwarning(title='Information', message="Please select devices from the network")
            self.parent.attributes('-disabled', 0)
        else:
            combo_string = self.combo.get()
            if combo_string != "Select a calibration procedure":
                cal_class = combo_string.replace(" ", '')
                eval(cal_class + '(self)')

            else:
                self.destroy()
                messagebox.showwarning(title='Information', message="Please select a calibration procedure from the "
                                                                    "drop-down menu")

    def on_closing(self):

        if messagebox.askokcancel("Quit", "Do you want to close the offsets calibration window?"):
            self.destroy()
            self.parent.attributes('-disabled', 0)
        else:
            pass
