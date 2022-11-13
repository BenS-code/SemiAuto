from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import threading
from ..general.devices import *
from ..general.create_directory import *


class Offsets(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.scroll_bar = None
        self.tv_offsets = None
        self.stop_btn = None
        self.start_btn = None
        self.status_entry = None
        self.progressbar = None
        self.progress_var = None
        self.wrapper3 = None
        self.wrapper2 = None
        self.wrapper1 = None
        self.parent = parent
        self.combo = parent.combo
        self.tv = parent.tv
        self.dir = parent.dir
        self.init_ui()

    def init_ui(self):

        self.wrapper1 = LabelFrame(self.parent, text=self.combo.get() + str(' - Calibration Window'))
        self.wrapper1.pack(side=TOP, fill="both", expand=1, padx=10, pady=10)
        self.wrapper2 = LabelFrame(self.parent, text='Status')
        self.wrapper2.pack(side=RIGHT, fill="both", expand=1, padx=10, pady=10)
        self.wrapper3 = LabelFrame(self.parent, text=self.combo.get() + str(' - Control Panel'))
        self.wrapper3.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        self.progress_var = DoubleVar()
        self.progressbar = ttk.Progressbar(self.wrapper2, style="green.Horizontal.TProgressbar",
                                           variable=self.progress_var)
        self.progressbar.pack(side=RIGHT, fill="x", expand=1, padx=10, pady=10)
        Label(self.wrapper2, text='Progress').pack(side=RIGHT)

        self.status_entry = Entry(self.wrapper2, borderwidth=2)
        self.status_entry.pack(side=RIGHT, fill="x", expand=1, padx=10, pady=10)
        Label(self.wrapper2, text='Status').pack(side=RIGHT)

        self.start_btn = Button(self.wrapper3, text='Start Calibration', command=self.on_start_btn)
        self.start_btn.config(state=NORMAL)
        self.start_btn.pack(side=RIGHT, padx=10, pady=10)

        self.stop_btn = Button(self.wrapper3, text='Stop Calibration', command=self.on_stop_btn)
        self.stop_btn.config(state=DISABLED)
        self.stop_btn.pack(side=RIGHT, padx=10, pady=10)

        self.tv_offsets = ttk.Treeview(self.wrapper1, columns=('1', '2', '3', '4', '5', '6',
                                                               '7', '8', '9', '10'),
                                       show="headings", height=16)
        self.tv_offsets.pack(side=LEFT, fill="both", expand=1, padx=10, pady=10)

        self.scroll_bar = ttk.Scrollbar(self.tv_offsets,
                                        orient="vertical",
                                        command=self.tv_offsets.yview)

        self.scroll_bar.pack(side='right', fill='y')

        self.tv_offsets.configure(yscrollcommand=self.scroll_bar.set)

        for col in self.tv_offsets['columns']:
            self.tv_offsets.column(col, width=20)  # set column width

        text_arr = ['SN', 'Channel', 'Average - AGC', 'STD - AGC', 'Average Emission', 'STD - Emission',
                    'Average Reflection', 'STD - Reflection', 'Gain', 'Status']

        for i in range(1, len(text_arr) + 1):
            self.tv_offsets.heading(i, text=text_arr[i - 1])
            self.tv_offsets.column(i, anchor=CENTER, stretch=YES, width=100)

        for child in self.tv.get_children():
            device_values = self.tv.item(child)['values']
            self.tv_offsets.insert('', END, values=(device_values[0], device_values[1],
                                                    '', '', '', '', '', '', '', "Ready"))

    def on_start_btn(self):
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)

        threads = []
        messagebox.showwarning(title='Message', message='Make sure that all units are stabilized and in the dark')

        self.parent.focus_force()

        for child in self.tv.get_children():
            cal_thread = OffsetsThread(self.parent, self, child,
                                       self.status_entry,
                                       self.progressbar,
                                       self.progress_var,
                                       self.dir)
            cal_thread.daemon = True
            threads.append(cal_thread)
            cal_thread.start()

        for t in threads:
            t.join()

    def on_stop_btn(self):
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)


class OffsetsThread(threading.Thread):
    def __init__(self, root, parent, child, status, progressbar, progress_var, directory):
        threading.Thread.__init__(self)

        self.samplingFreq = None
        self.root = root
        self.parent = parent
        self.child = child
        self.tv = root.tv
        self.tv_offsets = parent.tv_offsets
        self.status = status
        self.progressbar = progressbar
        self.progress_var = progress_var
        self.dir = directory
        [sn, ch, communication, port, ip, _, _,
         _, _, _] = self.tv.item(self.child)['values']
        self.ch = ch
        self.dev = NTM(communication, '', sn, ip, port)
        self.unit = self.dev.sn + '_' + self.ch
        self.status.delete(0, END)
        self.status.insert(END, "Calibrating unit: " + self.unit)
        self.directory_path = create_dir(self.unit, self.dir, "Offsets")

        if int(self.dev.dev_data['fw'][0]) >= 3:
            self.lph_min = int(0)
            self.lph_min_scale = int(0)
            self.min_limit = int(-32767)
            self.max_limit = int(32767)
        else:
            self.lph_min = int(32000)
            self.lph_min_scale = int(32000)
            self.min_limit = int(-2048)
            self.max_limit = int(2047)

        self.lock = threading.Lock()
        self.lock.acquire()
        self.run_thread()
        self.lock.release()

    def run_thread(self):
        self.tv_offsets.item(self.child, values=(self.dev.sn, self.ch, '', '', '',
                                                 '', '', '', '', 'Calibrating...'))
        print("\nCalibrating unit: " + self.unit)
        print('***************************************')
        self.parent.update_idletasks()
        self.initialize_unit()
        self.run_process()
        self.end_process()
        self.status.delete(0, END)
        self.status.insert(END, "Finished calibrating unit: " + self.unit)
        self.parent.update_idletasks()
        print("Done calibrating unit: " + self.unit)

    def initialize_unit(self):
        self.status.delete(0, END)
        self.status.insert(END, 'Initializing' + self.unit)
        self.parent.update_idletasks()

        # block writing to flush memory, close shutter, set maximum update rate
        self.dev.rxtx('ns2300=1|1103=1|301=1|')
        self.samplingFreq = round(1 / ((10 ** -6) * int(1)
                                       * int(self.dev.dev_data['cycle_time'])), 2)
        # turn-off LED
        self.dev.rxtx('ns2030=' + str(self.lph_min) + '|' +
                      '2031=' + str(self.lph_min_scale) + '|' +
                      '2130=' + str(self.lph_min) + '|' +
                      '2131=' + str(self.lph_min_scale) + '|')

        self.tv_offsets.item(self.child, values=(self.dev.sn, self.ch, '', '', '',
                                                 '', '', '', self.samplingFreq,
                                                 'Calibrating...'))

        time.sleep(1)

    def run_process(self):
        self.status.delete(0, END)
        self.status.insert(END, 'Starting offsets process of unit: ' + self.unit)
        self.parent.update_idletasks()

        samples = np.max([int(self.samplingFreq * 5), 100])
        signal_set_point = 0
        max_gain = self.dev.gain_table.index(str(self.dev.dev_gains_conf['max_gain']))
        min_limit = self.min_limit
        max_limit = self.max_limit

        if self.dev.dev_data['hw'] == 'Integrator':
            signal_workflow = ['agc_emission_', 'emission_', 'emission_', 'reflection_',
                               'agc_emission_', 'emission_', 'emission_',
                               'agc_emission_', 'emission_', 'emission_', 'reflection_']
            gain_index_workflow = [10, 10, 1, 10, 6, 6, 1, 11, 11, 1, 11]
            gain_mode_workflow = [1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3]
            cmd_workflow = ['2035', '2040', '2037', '2038', '2036', '2046', '2039', '2041', '1211', '1221', '1222']
            param_workflow = ['offset_in_IL', 'offset_rf_IL', 'offset_a2d_emission_IL', 'offset_a2d_emissivity_IL',
                              'offset_in_IS', 'offset_rf_IS', 'offset_a2d_emission_IS',
                              'offset_in_RC', 'offset_rf_RC', 'offset_a2d_emission_RC', 'offset_a2d_emissivity_RC']

        else:
            signal_workflow = ['agc_emission_', 'agc_emission_', 'emission_', 'emission_', 'reflection_']
            gain_index_workflow = [max_gain, max_gain, 1, max_gain, max_gain]
            gain_mode_workflow = [0, 1, 0, 0, 0]
            param_workflow = ['offset_in_' + self.ch, 'offset_in_scale_' + self.ch,
                              'offset_a2d_emission_' + self.ch,
                              'offset_rf_' + self.ch, 'offset_a2d_emissivity_' + self.ch]

            if self.ch == 'ch1':
                cmd_workflow = ['2035', '2041', '2037', '2040', '2038']

            else:
                cmd_workflow = ['2036', '2047', '2039', '2046', '2138']

        for i in range(0, len(signal_workflow)):

            self.dev.set_signal_value(signal_workflow[i], self.ch, min_limit,
                                      max_limit, gain_index_workflow[i],
                                      gain_mode_workflow[i], samples, signal_set_point,
                                      cmd_workflow[i], param_workflow[i])

        self.parent.update_idletasks()

    def end_process(self):
        self.status.delete(0, END)
        self.status.insert(END, 'Ending offsets process of unit: ' + self.unit)
        self.parent.update_idletasks()

        self.status.delete(0, END)
        self.status.insert(END, 'Restoring initial parameters of unit: ' + self.unit)
        self.parent.update_idletasks()

        # restore LPH
        self.dev.rxtx('ns2030=' + str(self.dev.dev_lph_conf['lph_ch1']) + '|' +
                      '2031=' + str(self.dev.dev_lph_conf['lph_ch1_scale']) + '|' +
                      '2130=' + str(self.dev.dev_lph_conf['lph_ch2']) + '|' +
                      '2131=' + str(self.dev.dev_lph_conf['lph_ch2_scale']) + '|')

        # restore automatic gains
        self.dev.rxtx('ns501=0|' +
                      '508=0|' +
                      '510=0|' +
                      '516=0|' +
                      '1201=0|')

        # allow writing to flush memory, open shutter, restore update rate
        self.dev.rxtx('ns2300=0|1103=0|301=' + str(self.dev.dev_data['update_rate_code']) + '|')

        self.tv_offsets.item(self.child, values=(self.dev.sn, self.ch, '', '', '',
                                                 '', '', '', self.dev.dev_data['update_rate'], 'Done'))

        time.sleep(1)
