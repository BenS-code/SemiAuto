from tkinter import *
from tkinter import ttk, messagebox
from semiautoapp.semimodules.general.devices import *
from semiautoapp.semimodules.general.communication import *
import pandas as pd


class FindDev(Toplevel):
    def __init__(self, parent, port, time_out, data):
        super().__init__(parent)

        self.cb_serial = None
        self.dev = None
        self.parent = parent
        self.communication = parent.var.get()
        self.port = port
        self.data = data
        self.time_out = time_out
        self.tv = parent.tv
        self.refresh_dev_win_btn = None
        self.close_dev_win_btn = None
        self.add_device_btn = None
        self.tree_scroll = None
        self.tv_dev = None
        self.wrapper = None
        self.export_params_btn = parent.export_params_btn
        self.grab_set()
        if self.communication == 1:
            self.init_ui_lan()
            self.show_devices()
        elif self.communication == 2:
            self.init_ui_rs232()

    def init_ui_lan(self):

        self.title("List of devices on the network")
        self.geometry('800x360')
        self.minsize(400, 360)
        self.resizable(width=False, height=True)

        self.wrapper = LabelFrame(self, text="Devices on the network")
        self.wrapper.pack(fill="both", expand=1, padx=10, pady=10)

        self.tv_dev = ttk.Treeview(self.wrapper, columns=('1', '2'), show="headings")
        self.tv_dev.pack(fill="both", expand=1, padx=10, pady=10)

        self.tree_scroll = ttk.Scrollbar(self.tv_dev)
        self.tree_scroll.configure(command=self.tv_dev.yview)
        self.tv_dev.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side=RIGHT, fill=BOTH)

        tv_dev_headings = ['SN', 'IP/COM']

        for j in range(1, 3):
            self.tv_dev.heading(j, text=tv_dev_headings[j - 1])
            self.tv_dev.column(j, anchor=CENTER, stretch=YES)

        self.add_device_btn = Button(self.wrapper, text='Add device', width=10, command=self.add_device)
        self.add_device_btn.config(state=NORMAL)
        self.add_device_btn.pack(side=RIGHT, padx=10, pady=10)

        self.refresh_dev_win_btn = Button(self.wrapper, text='Refresh', width=10, command=self.show_devices)
        self.refresh_dev_win_btn.config(state=NORMAL)
        self.refresh_dev_win_btn.pack(side=RIGHT, padx=10, pady=10)

        self.close_dev_win_btn = Button(self.wrapper, text='Close', width=10, command=self.destroy)
        self.close_dev_win_btn.config(state=NORMAL)
        self.close_dev_win_btn.pack(side=RIGHT, padx=10, pady=10)

    def init_ui_rs232(self):
        self.title("List of devices on the network")
        self.geometry('400x120')
        self.minsize(400, 120)
        self.resizable(width=False, height=False)

        self.wrapper = LabelFrame(self, text="Devices on COM ports")
        self.wrapper.pack(fill="both", expand=1, padx=10, pady=10)

        self.cb_serial = ttk.Combobox(self.wrapper, values=RS232().show_ports())
        self.cb_serial.pack(side=LEFT, padx=10, pady=10)

        self.add_device_btn = Button(self.wrapper, text='Add device', width=10, command=self.add_device)
        self.add_device_btn.config(state=NORMAL)
        self.add_device_btn.pack(side=LEFT, padx=10, pady=10)

        self.close_dev_win_btn = Button(self.wrapper, text='Close', width=10, command=self.destroy)
        self.close_dev_win_btn.config(state=NORMAL)
        self.close_dev_win_btn.pack(side=RIGHT, padx=10, pady=10)

    def show_devices(self):
        self.tv_dev.delete(*self.tv_dev.get_children())
        [ports, sn_list, ip_list] = LAN(self.port,
                                        self.time_out,
                                        self.data).find_device()  # b'nw' -ntm # b'ow' -tts

        df = pd.DataFrame({'SNnIP': ports, "SN": sn_list, 'IP/COM': ip_list})
        df = df.sort_values(by='SN', ascending=True).reset_index(drop=True)
        df_duplicates = df[df['IP/COM'].duplicated(keep=False)]
        if not df_duplicates.empty:
            messagebox.showwarning(title='Warning', message=f"Duplicate ip identified! -\n"
                                                            f" {df_duplicates['SNnIP'].values}")
        for j in range(len(df)):
            self.tv_dev.insert('', END, values=[df["SN"][j], df["IP/COM"][j]])

    def add_device(self):
        if self.communication == 1:
            for selected_item in self.tv_dev.selection():
                [sn, ip] = self.tv_dev.item(selected_item, 'values')
                self.dev = NTM('LAN', '', sn, ip, self.port)

                if self.dev.dev_data['single_dual'] == 'Dual':
                    number_of_channels = 2
                else:
                    number_of_channels = 1

                for i in range(number_of_channels):
                    ch = 'ch' + str(i + 1)
                    values = [self.dev.sn, ch, self.dev.communication, self.dev.port, self.dev.ip, self.dev.dev_data['fw'],
                              self.dev.dev_data['hw'], self.dev.dev_data['dev_type'], self.dev.dev_data['single_dual'],
                              self.dev.dev_data['update_rate']]
                    tv_values = []
                    dev_str = self.dev.sn + '_' + ch
                    print(values)
                    for child in self.tv.get_children():
                        tv_values.append(self.tv.item(child)["values"][0] + '_' + self.tv.item(child)["values"][1])

                    if dev_str not in tv_values:
                        if len(self.tv.get_children()) > 15:
                            messagebox.showwarning(title='Information',
                                                   message="The device list is limited to 16 channels")
                        else:
                            self.tv.insert('', END, values=values)
                            for child in self.tv.get_children():
                                tv_values.append(self.tv.item(child)["values"][0] + '_' + self.tv.item(child)["values"][1])
                    else:
                        messagebox.showwarning(title='Information', message="Unit is already in the device list")
                        break

            if self.tv.get_children():
                self.export_params_btn.config(state=NORMAL)

            elif self.communication == 2:
                self.dev = NTM('', 'RS232', '', '', self.port)
                print(self.dev)
