import pandas as pd
from ..general.devices import *
from ..general.create_directory import *
from semiautoapp.semimodules.general.communication import *
import concurrent.futures


class ExportParams:
    def __init__(self, tv, directory_entry):
        super().__init__()

        self.tv = tv
        self.dir = directory_entry
        self.export_params()

    def export_params(self):
        devs = []
        for selected_item in self.tv.selection():
            device_values = self.tv.item(selected_item)['values']
            [sn, _, comm, port, ip, _,  _,
             _, _, _] = device_values
            if comm == 'LAN':
                devs.append(NTM(comm, '', sn, ip, port))
            elif comm == 'RS232':
                devs.append(NTM(comm, RS232().connect_serial(port), sn, ip, ''))

        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for dev in devs:
                futures.append(executor.submit(dev.get_full_parameters))
                file_path = create_dir(dev.sn, self.dir.get(), "Parameters")
                for future in concurrent.futures.as_completed(futures):
                    dictionary = {'Code': future.result()[2], 'Value': future.result()[1]}
                df = pd.DataFrame(dictionary)
                df.to_csv(f'{file_path}/{dev.sn}_parameters.csv', index=False)
                print(future.result()[0])
