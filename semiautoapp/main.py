from tkinter import filedialog
from os import getcwd
from semiautoapp.semimodules.general import *
from semiautoapp.semimodules.calibration_processes import *


class GUI(Tk):
    def __init__(self):
        super().__init__()

        self.port = None
        self.my_frame = Frame(self)
        self.my_frame.pack()

        self.title("CI SEMI - Automated Integration Software")
        self.geometry('1250x400')
        self.minsize(1250, 400)
        self.resizable(width=False, height=False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # self.option_add('*Font', 'Ariel 10')

        self.wrapper1 = LabelFrame(self.master, text="Device List")
        self.wrapper1.pack(side=TOP, fill="both", expand=1, padx=10, pady=10)

        self.wrapper2 = LabelFrame(self.master, text="Calibration Option")
        self.wrapper2.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        self.wrapper3 = LabelFrame(self.master, text="Export Folder")
        self.wrapper3.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        self.tv = ttk.Treeview(self.wrapper1, columns=('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'),
                               show="headings", height=16)
        self.tv.pack(side=TOP, fill="both", expand=1, padx=10, pady=10)

        scroll_bar = ttk.Scrollbar(self.tv,
                                   orient="vertical",
                                   command=self.tv.yview)

        scroll_bar.pack(side='right', fill='y')

        self.tv.configure(yscrollcommand=scroll_bar.set)

        text_arr = ['SN', 'Channel', 'Communication', 'Port/COM', 'IP', 'Firmware', 'Hardware', 'Type',
                    'Single/Dual', 'Update Rate']

        for i in range(1, len(text_arr) + 1):
            self.tv.heading(i, text=text_arr[i - 1])
            self.tv.column(i, anchor=CENTER, stretch=YES, width=100)

        self.find_ntm_btn = Button(self.wrapper1, text='Find NTM units', width=15,
                                   command=lambda: self.find_ntm())
        self.find_ntm_btn.config(state=NORMAL)
        self.find_ntm_btn.pack(side=RIGHT, padx=10, pady=10)

        self.find_tts_btn = Button(self.wrapper1, text='Find TTS units', width=15,
                                   command=lambda: self.find_tts())
        self.find_tts_btn.config(state=NORMAL)
        self.find_tts_btn.pack(side=RIGHT, padx=10, pady=10)

        self.remove_device_btn = Button(self.wrapper1, text='Remove device', width=15,
                                        command=lambda: self.remove_item())
        self.remove_device_btn.config(state=NORMAL)
        self.remove_device_btn.pack(side=RIGHT, padx=10, pady=10)

        self.remove_all_btn = Button(self.wrapper1, text='Clear Table', width=15,
                                     command=lambda: self.clear_table())
        self.remove_all_btn.config(state=NORMAL)
        self.remove_all_btn.pack(side=RIGHT, padx=10, pady=10)

        self.export_params_btn = Button(self.wrapper1, text='Export parameters', width=15,
                                        command=self.export_params)
        self.export_params_btn.config(state=DISABLED)
        self.export_params_btn.pack(side=RIGHT, padx=10, pady=10)

        cal_list = ['Offsets', 'Gain Multiplier', 'Cross Talk', 'Noise Spectrum', 'Emission STD',
                    'Temperature Calibration', 'Response procedure']
        self.combo = ttk.Combobox(self.wrapper2, values=cal_list)
        self.combo.set("Select a calibration procedure")
        self.combo.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        self.run_btn = Button(self.wrapper2, text='Open Calibration Window', command=lambda: CalibrationWin(self))
        self.run_btn.config(state=NORMAL)
        self.run_btn.pack(side=LEFT, padx=10, pady=10)

        # directory entry
        self.directory_entry = Entry(self.wrapper3, borderwidth=1)
        self.directory_entry.insert(END, getcwd())
        self.directory_entry.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        # browse directory
        self.directory_btn = Button(self.wrapper3, text='Browse', command=lambda: self.browse_button())
        self.directory_btn.config(state=NORMAL)
        self.directory_btn.pack(side=RIGHT, padx=10, pady=10)

        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.map("Treeview")
        # style.configure("Treeview.Heading", font=("Ariel", 10))

    def on_closing(self):

        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
        else:
            pass

    def browse_button(self):

        folder_destination = StringVar()
        filename = filedialog.askdirectory()
        folder_destination.set(filename)
        if filename:
            self.directory_entry.delete(0, END)
            self.directory_entry.insert(0, filename)

    def remove_item(self):
        for selected_item in self.tv.selection():
            self.tv.delete(selected_item)

        if not self.tv.get_children():
            self.export_params_btn.config(state=DISABLED)

    def clear_table(self):
        self.tv.delete(*self.tv.get_children())
        self.export_params_btn.config(state=DISABLED)

    def find_ntm(self):
        port = 50000
        data = b'nw'
        time_out = 0.05
        FindDev(self, port, time_out, data)

    def find_tts(self):
        port = 50003
        data = b'ow'
        time_out = 0.05
        FindDev(self, port, time_out, data)

    def export_params(self):
        ExportParams(self.tv)


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
