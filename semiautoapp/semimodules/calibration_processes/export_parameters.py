from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import threading
from ..general.devices import *
from ..general.create_directory import *
import concurrent.futures


class ExportParams:
    def __init__(self, tv):
        super().__init__()

        self.tv = tv
        self.export_params()

    def export_params(self):
        devs = []
        for selected_item in self.tv.selection():
            device_values = self.tv.item(selected_item)['values']
            [sn, _, comm, port, ip, _, _,
             _, _, _] = device_values
            devs.append(NTM(comm, '', sn, ip, port))

        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for dev in devs:
                futures.append(executor.submit(dev.get_full_parameters))
            for future in concurrent.futures.as_completed(futures):
                print(future.result())

            # t = threading.Thread(target=dev.get_full_parameters())
            # t.start()
            # threads.append(t)
        #
        # for thread in threads:
        #     thread.join()
