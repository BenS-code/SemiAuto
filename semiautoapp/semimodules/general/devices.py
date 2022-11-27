from socket import *
import struct
import numpy as np
import time


class NTM:

    def __init__(self, communication, com_port, sn, ip, port):

        # set defaults

        self.dev_data = {'sn': '', 'dev_type': '', 'single_dual': '', 'hw': '', 'fw': '', 'update_rate': 10,
                         'cycle_time': 100000, 'update_rate_code': 1}

        self.dev_gains_conf = {'gain_ch1': 0, 'gain_ch2': 0, 'is_scale_ch1': 0, 'is_scale_ch2': 0,
                               'integrator_mode': 0, 'is_integrator_mode': 0, 'max_gain': 8000}

        self.dev_lph_conf = {'lph_ch1': 32000, 'lph_ch1_scale': 32000, 'lph_ch2': 32000, 'lph_ch2_scale': 32000,
                             'max_lph_ch1': 65535, 'max_lph_ch1_scale': 65535, 'max_lph_ch2': 65535,
                             'max_lph_ch2_scale': 65535, 'is_lph_sync': 0}

        self.dev_offsets = {'offset_in_IL': 0, 'offset_in_IS': 0, 'offset_in_RC': 0, 'offset_rf_IL': 0.0,
                            'offset_rf_IS': 0.0, 'offset_a2d_emission_IL': 0, 'offset_a2d_emissivity_IL': 0,
                            'offset_a2d_emission_IS': 0, 'offset_rf_RC': 0.0, 'offset_a2d_emission_RC': 0,
                            'offset_a2d_emissivity_RC': 0, 'offset_in_ch1': 0, 'offset_in_ch2': 0,
                            'offset_in_scale_ch1': 0, 'offset_rf_ch1': 0.0, 'offset_in_scale_ch2': 0,
                            'offset_rf_ch2': 0.0, 'offset_a2d_emission_ch1': 0, 'offset_a2d_emissivity_ch1': 0,
                            'offset_a2d_emission_ch2': 0, 'offset_a2d_emissivity_ch2': 0}

        self.dev_signals = {'time': [], 'temperature_ch1': [], 'emissivity_ch1': [], 'emission_ch1': [],
                            'temperature_ch2': [], 'emissivity_ch2': [], 'emission_ch2': [],
                            'reflection_ch1': [], 'reflection_ch2': [], 'board_t': [], 'thermos_t': [],
                            'gain_ch1': [], 'agc_emission_ch1': [], 'gain_ch2': [], 'agc_emission_ch2': []}

        self.gain_table = ['AGC', '1', '2', '4', '8', '10', '20', '40', '80', '100',
                           '200', '400', '800', '1000', '2000', '4000', '8000']

        self.communication = communication
        self.com_port = com_port
        self.sn = sn
        self.ip = ip
        self.port = port
        self.udp_client_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.udp_client_socket.settimeout(2)
        self.buffer_size = 1024

        self.get_device_data()
        self.get_gain_settings()
        self.get_lph_settings()
        self.get_offsets_settings()

    def rxtx(self, command):

        if self.communication == 'LAN':

            bytes_to_send = str.encode(command)
            server_address_port = (self.ip, self.port)

            self.udp_client_socket.sendto(bytes_to_send, server_address_port)

            results = []
            code_number = []
            try:
                [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)
                if command == 'dts':
                    while not (data == b'DTOK\n' or data == b'DTErr\n'):
                        [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)

                # print(self.sn + ' - sent data:', command)
                # print(self.sn + ' - received data:', data)

                split_data = data.decode('ISO-8859-1')[2:].split('|')
                split_data = split_data[:-1]
                try:
                    for i in split_data:
                        results.append(i.split('=')[1])
                        code_number.append(i.split('=')[0])

                except IndexError:
                    print('Problem occurred in data received')

                return results, code_number
            except error:

                print("Could not connect with the LAN-port")
                data = "Error"
                return data

        elif self.communication == 'RS232':

            # checksum algorithm
            hex_num = hex(sum(command.encode('ISO-8859-1')) % 256).rstrip("L").lstrip("0x")
            if len(hex_num) == 1:
                hex_num = '0' + hex_num
            checksum = bytes.fromhex(hex_num)

            # data to send
            send_data = command.encode('ISO-8859-1') + b'\x00' + checksum + b'\n\n\n'

            # write to device
            self.com_port.write(send_data)
            results = []
            code_number = []
            try:
                data = self.com_port.readline() + self.com_port.readline() + self.com_port.readline()

                split_data = data.decode('ISO-8859-1')[2:].split('|')
                for i in split_data[:-1]:
                    results.append(i.split('=')[1])
                    code_number.append(i.split('=')[0])

                # print('sent data:', command)
                # print('received data:', data)
                return results, code_number

            except error:

                print("Could not connect with the serial-port")
                data = "Error"
                return data

    def get_full_parameters(self):
        codes = []
        values = []
        if (self.port == 50000) or (self.port == 50003):
            cmd = 'nr'
        else:
            cmd = ''
        print('\nExporting parameters... ')

        tic = time.time()
        N_commands = 10
        for i in range(100, 4100, N_commands):
            command = cmd
            for j in range(N_commands):
                command = command + str(i+j) + '|'
            [value, code] = self.rxtx(command)
            values.append(value)
            codes.append(code)
        toc = time.time()
        codes = np.hstack(codes)
        values = np.hstack(values)

        return f'done in {toc-tic}', values, codes

    def get_device_data(self):
        [data, _] = self.rxtx('nr301|1001|106|1126|1120|101|102|')
        update_rate_code = int(data[0])
        cycle_time = int(data[1])
        update_rate = round(1 / ((10 ** -6) * update_rate_code * cycle_time), 2)
        dev_type = str(data[2])
        single_dual = int(data[3])
        hw = int(data[4])
        fw = str(data[5])
        sn = str(data[6])

        if hw == 1:
            hw = 'Integrator'
        elif hw == 0:
            hw = 'Standard'

        if single_dual == 1:
            single_dual = 'Dual'
        elif single_dual == 0:
            single_dual = 'Single'

        self.sn = sn
        self.dev_data['sn'] = sn
        self.dev_data['dev_type'] = dev_type
        self.dev_data['single_dual'] = single_dual
        self.dev_data['hw'] = hw
        self.dev_data['fw'] = fw
        self.dev_data['update_rate'] = update_rate
        self.dev_data['cycle_time'] = cycle_time
        self.dev_data['update_rate_code'] = update_rate_code

    def get_gain_settings(self):

        [data, _] = self.rxtx('nr501|508|510|516|1201|1120|561|')

        self.dev_gains_conf['gain_ch1'] = int(data[0])
        self.dev_gains_conf['gain_ch2'] = int(data[1])
        self.dev_gains_conf['is_scale_ch1'] = int(data[2])
        self.dev_gains_conf['is_scale_ch2'] = int(data[3])
        self.dev_gains_conf['integrator_mode'] = int(data[4])
        self.dev_gains_conf['is_integrator_mode'] = int(data[5])

        try:
            self.dev_gains_conf['max_gain'] = int(data[6])
        except IndexError:
            print('Max gain (code 561) is not defined in this fw - return default 8000')
            self.dev_gains_conf['max_gain'] = int(8000)

    def get_lph_settings(self):

        [data, _] = self.rxtx('nr2030|2031|2130|2131|2170|2171|2172|2173|2083|')

        self.dev_lph_conf['lph_ch1'] = int(data[0])
        self.dev_lph_conf['lph_ch1_scale'] = int(data[1])
        self.dev_lph_conf['lph_ch2'] = int(data[2])
        self.dev_lph_conf['lph_ch2_scale'] = int(data[3])
        self.dev_lph_conf['max_lph_ch1'] = int(data[4])
        self.dev_lph_conf['max_lph_ch1_scale'] = int(data[5])
        self.dev_lph_conf['max_lph_ch2'] = int(data[6])
        self.dev_lph_conf['max_lph_ch2_scale'] = int(data[7])
        self.dev_lph_conf['is_lph_sync'] = int(data[8])

    def get_offsets_settings(self):
        [data, _] = self.rxtx('nr2035|2036|2041|2040|2047|2046|2037|2038|2039|2138|1211|1221|1222|')

        if self.dev_gains_conf['is_integrator_mode'] == 1:
            self.dev_offsets['offset_in_IL'] = int(data[0])
            self.dev_offsets['offset_in_IS'] = int(data[1])
            self.dev_offsets['offset_in_RC'] = int(data[2])
            self.dev_offsets['offset_rf_IL'] = float(data[3])
            self.dev_offsets['offset_rf_IS'] = float(data[5])
            self.dev_offsets['offset_a2d_emission_IL'] = int(data[6])
            self.dev_offsets['offset_a2d_emissivity_IL'] = int(data[7])
            self.dev_offsets['offset_a2d_emission_IS'] = int(data[8])
            self.dev_offsets['offset_rf_RC'] = float(data[10])
            self.dev_offsets['offset_a2d_emission_RC'] = int(data[11])
            self.dev_offsets['offset_a2d_emissivity_RC'] = int(data[12])

        else:
            self.dev_offsets['offset_in_ch1'] = int(data[0])
            self.dev_offsets['offset_in_ch2'] = int(data[1])
            self.dev_offsets['offset_in_scale_ch1'] = int(data[2])
            self.dev_offsets['offset_rf_ch1'] = float(data[3])
            self.dev_offsets['offset_in_scale_ch2'] = int(data[4])
            self.dev_offsets['offset_rf_ch2'] = float(data[5])
            self.dev_offsets['offset_a2d_emission_ch1'] = int(data[6])
            self.dev_offsets['offset_a2d_emissivity_ch1'] = int(data[7])
            self.dev_offsets['offset_a2d_emission_ch2'] = int(data[8])
            self.dev_offsets['offset_a2d_emissivity_ch2'] = int(data[9])

    def set_gain_settings(self, mode, gain_index, ch):

        """
        standard HW:
        normal/scale => mode = 0/1

        Integrator HW:
        AGC/IL/IS/RC => mode = 0/1/2/3

         gain_index = index{[AGC, 1, 2, 4, 8, 10, 20, 40, 80, 100, 200, 400, 800, 1000, 2000, 4000, 8000]}
         index =............[.0.,.1,.2,.3,.4,.5.,.6.,.7.,.8.,.9..,.10.,.11.,.12.,..13.,..14.,..15.,..16.]
        """

        if self.dev_data['hw'] == 'Standard':
            if ch == 'ch1':
                param = '501'
                code = '510'
            else:
                param = '508'
                code = '516'

        elif self.dev_data['hw'] == 'Integrator':
            param = '501'
            code = '1201'
        else:
            param = '501'
            code = '510'

        self.rxtx('ns' + code + '=' + str(mode) + '|' + str(param) + '=' + str(gain_index) + '|')

    def send_full_packet(self, auto):
        # auto = 1 -> single packet
        # auto = 0 -> continuous packets

        full_packet = 'dtr' + str(auto) + '|'
        for i in range(1, 63):
            full_packet = full_packet + str(i) + '|'

        # print(self.sn + ' - sent data:', full_packet)

        self.udp_client_socket.sendto(str.encode(full_packet), (self.ip, self.port))

    def receive_full_packet(self):

        try:
            [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)
            # print(self.sn + ' - received data:', data)

        except error:

            print("Communication error - reading packet again")
            self.send_full_packet(0)
            [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)
            # print(self.sn + ' - received data:', data)

        if self.dev_data['single_dual'] == 'Dual':
            self.dev_signals['time'].append(struct.unpack('<f', bytes.fromhex(data.hex()[6:14]))[0])
            self.dev_signals['temperature_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[16:24]))[0])
            self.dev_signals['emissivity_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[26:34]))[0])
            self.dev_signals['emission_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[36:44]))[0])
            self.dev_signals['temperature_ch2'].append(struct.unpack('<f', bytes.fromhex(data.hex()[46:54]))[0])
            self.dev_signals['emissivity_ch2'].append(struct.unpack('<f', bytes.fromhex(data.hex()[56:64]))[0])
            self.dev_signals['emission_ch2'].append(struct.unpack('<f', bytes.fromhex(data.hex()[66:74]))[0])
            self.dev_signals['reflection_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[126:134]))[0])
            self.dev_signals['reflection_ch2'].append(struct.unpack('<f', bytes.fromhex(data.hex()[136:144]))[0])
            self.dev_signals['board_t'].append(struct.unpack('<i', bytes.fromhex(data.hex()[196:204]))[0])
            self.dev_signals['thermos_t'].append(struct.unpack('<i', bytes.fromhex(data.hex()[206:214]))[0])
            self.dev_signals['gain_ch1'].append(struct.unpack('<i', bytes.fromhex(data.hex()[216:224]))[0])
            self.dev_signals['agc_emission_ch1'].append(struct.unpack('<i', bytes.fromhex(data.hex()[226:234]))[0])
            self.dev_signals['gain_ch2'].append(struct.unpack('<i', bytes.fromhex(data.hex()[236:238] + '000000'))[0])
            self.dev_signals['agc_emission_ch2'].append(struct.unpack('<i', bytes.fromhex(data.hex()[238:244]
                                                                                          + data.hex()[242:244]))[0])

            # print('\nTime = ', self.time[-1])
            # print('Temperature_ch1 = ', self.temperature_ch1[-1])
            # print('Emissivity_ch1 = ', self.emissivity_ch1[-1])
            # print('Emission_ch1 = ', self.emission_ch1[-1])
            # print('Temperature_ch2 = ', self.temperature_ch2[-1])
            # print('Emissivity_ch2 = ', self.emissivity_ch2[-1])
            # print('Emission_ch2 = ', self.emission_ch2[-1])
            # print('Reflection_ch1 = ', self.reflection_ch1[-1])
            # print('Reflection_ch2 = ', self.reflection_ch2[-1])
            # print('BoardT = ', self.board_t[-1] * 0.1245 - 255.6)
            # print('ThermosT = ', self.thermos_t[-1] * 0.111 - 273)
            # print('Gain_ch1 = ', self.gain_ch1[-1])
            # print('AGC_emission_ch1 = ', self.agc_emission_ch1[-1])
            # print('Gain_ch2 = ', self.gain_ch2[-1])
            # print('AGC_emission_ch2 = ', self.agc_emission_ch2[-1], '\n')

        elif self.dev_data['single_dual'] == 'Single':
            self.dev_signals['time'].append(struct.unpack('<f', bytes.fromhex(data.hex()[6:14]))[0])
            self.dev_signals['temperature_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[16:24]))[0])
            self.dev_signals['emissivity_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[26:34]))[0])
            self.dev_signals['emission_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[36:44]))[0])
            self.dev_signals['reflection_ch1'].append(struct.unpack('<f', bytes.fromhex(data.hex()[76:84]))[0])
            self.dev_signals['board_t'].append(struct.unpack('<i', bytes.fromhex(data.hex()[136:144]))[0])
            self.dev_signals['thermos_t'].append(struct.unpack('<i', bytes.fromhex(data.hex()[146:154]))[0])
            self.dev_signals['gain_ch1'].append(struct.unpack('<i', bytes.fromhex(data.hex()[156:164]))[0])
            self.dev_signals['agc_emission_ch1'].append(struct.unpack('<i', bytes.fromhex(data.hex()[166:174]))[0])

            # print('\nTime = ', self.time[-1])
            # print('Temperature_ch1 = ', self.temperature_ch1[-1])
            # print('Emissivity_ch1 = ', self.emissivity_ch1[-1])
            # print('Emission_ch1 = ', self.emission_ch1[-1])
            # print('Reflection_ch1 = ', self.reflection_ch1[-1])
            # print('BoardT = ', self.board_t[-1] * 0.1245 - 255.6)
            # print('ThermosT = ', self.thermos_t[-1] * 0.111 - 273)
            # print('Gain_ch1 = ', self.gain_ch1[-1])
            # print('AGC_emission_ch1 = ', self.agc_emission_ch1[-1])

    def initiate_signals(self):

        self.dev_signals['time'] = []
        self.dev_signals['temperature_ch1'] = []
        self.dev_signals['emissivity_ch1'] = []
        self.dev_signals['emission_ch1'] = []
        self.dev_signals['temperature_ch2'] = []
        self.dev_signals['emissivity_ch2'] = []
        self.dev_signals['emission_ch2'] = []
        self.dev_signals['reflection_ch1'] = []
        self.dev_signals['reflection_ch2'] = []
        self.dev_signals['board_t'] = []
        self.dev_signals['thermos_t'] = []
        self.dev_signals['gain_ch1'] = []
        self.dev_signals['agc_emission_ch1'] = []
        self.dev_signals['gain_ch2'] = []
        self.dev_signals['agc_emission_ch2'] = []

    def signals_statistics(self, samples):

        self.initiate_signals()

        self.send_full_packet(0)

        for i in range(samples):
            self.receive_full_packet()

        self.rxtx('dts')

        if self.dev_data['single_dual'] == 'Dual':
            return {'time': [np.mean(self.dev_signals['time']), np.std(self.dev_signals['time'])],
                    'temperature_ch1': [np.mean(self.dev_signals['temperature_ch1']),
                                        np.std(self.dev_signals['temperature_ch1'])],
                    'emissivity_ch1': [np.mean(self.dev_signals['emissivity_ch1']),
                                       np.std(self.dev_signals['emissivity_ch1'])],
                    'emission_ch1': [np.mean(self.dev_signals['emission_ch1']),
                                     np.std(self.dev_signals['emission_ch1'])],
                    'reflection_ch1': [np.mean(self.dev_signals['reflection_ch1']),
                                       np.std(self.dev_signals['reflection_ch1'])],
                    'temperature_ch2': [np.mean(self.dev_signals['temperature_ch2']),
                                        np.std(self.dev_signals['temperature_ch2'])],
                    'emissivity_ch2': [np.mean(self.dev_signals['emissivity_ch2']),
                                       np.std(self.dev_signals['emissivity_ch2'])],
                    'emission_ch2': [np.mean(self.dev_signals['emission_ch2']),
                                     np.std(self.dev_signals['emission_ch2'])],
                    'reflection_ch2': [np.mean(self.dev_signals['reflection_ch2']),
                                       np.std(self.dev_signals['reflection_ch2'])],
                    'board_t': [np.mean(self.dev_signals['board_t']),
                                np.std(self.dev_signals['board_t'])],
                    'thermos_t': [np.mean(self.dev_signals['thermos_t']),
                                  np.std(self.dev_signals['thermos_t'])],
                    'gain_ch1': [np.mean(self.dev_signals['gain_ch1']),
                                 np.std(self.dev_signals['gain_ch1'])],
                    'agc_emission_ch1': [np.mean(self.dev_signals['agc_emission_ch1']),
                                         np.std(self.dev_signals['agc_emission_ch1'])],
                    'gain_ch2': [np.mean(self.dev_signals['gain_ch2']),
                                 np.std(self.dev_signals['gain_ch2'])],
                    'agc_emission_ch2': [np.mean(self.dev_signals['agc_emission_ch2']),
                                         np.std(self.dev_signals['agc_emission_ch2'])]}

        elif self.dev_data['single_dual'] == 'Single':
            return {'time': [np.mean(self.dev_signals['time']),
                             np.std(self.dev_signals['time'])],
                    'temperature_ch1': [np.mean(self.dev_signals['temperature_ch1']),
                                        np.std(self.dev_signals['temperature_ch1'])],
                    'emissivity_ch1': [np.mean(self.dev_signals['emissivity_ch1']),
                                       np.std(self.dev_signals['emissivity_ch1'])],
                    'emission_ch1': [np.mean(self.dev_signals['emission_ch1']),
                                     np.std(self.dev_signals['emission_ch1'])],
                    'reflection_ch1': [np.mean(self.dev_signals['reflection_ch1']),
                                       np.std(self.dev_signals['reflection_ch1'])],
                    'board_t': [np.mean(self.dev_signals['board_t']),
                                np.std(self.dev_signals['board_t'])],
                    'thermos_t': [np.mean(self.dev_signals['thermos_t']),
                                  np.std(self.dev_signals['thermos_t'])],
                    'gain_ch1': [np.mean(self.dev_signals['gain_ch1']),
                                 np.std(self.dev_signals['gain_ch1'])],
                    'agc_emission_ch1': [np.mean(self.dev_signals['agc_emission_ch1']),
                                         np.std(self.dev_signals['agc_emission_ch1'])]}

    def set_signal_value(self, signal, ch, min_limit, max_limit, gain, gain_mode, samples,
                         set_point, param_code, param_str):

        self.set_gain_settings(gain_mode, gain, ch)

        time.sleep(0.2)

        stat_data = self.signals_statistics(samples)

        signal_average = float(stat_data[signal + ch][0])
        signal_std = float(stat_data[signal + ch][1])

        min_ref = set_point - 1 * np.min([(signal_std / 2), 1])
        max_ref = set_point + 1 * np.min([(signal_std / 2), 1])

        param_value = self.dev_offsets[param_str]

        print('\n' + signal + ch + ' (' + str(samples) + ' samples)')
        print('-----------------------------------------------')
        print('Average: ', signal_average)
        print('STD: ', signal_std)
        print('Set-point: ', set_point)
        print('Set-point low limit: ', min_ref)
        print('Set-point high limit: ', max_ref)
        print('Gain mode: ', gain_mode)
        print('Gain index: ', gain)
        print(param_str + ': ' + str(param_value))
        print('-----------------------------------------------\n')

        if type(param_value) == int:
            print('Binary search:')
            print('--------------------')
            self.binary_search(signal, ch, min_limit, max_limit, min_ref, max_ref,
                               param_code, param_str, samples, set_point)
        elif type(param_value) == float:
            print('Average acquisition:')
            print('-------------------------')
            statistics_data = self.signals_statistics(3 * samples)
            signal_average = float(statistics_data[signal + ch][0])
            self.rxtx('ns' + param_code + '=' + str(float(signal_average) + float(param_value)) + '|')

    def binary_search(self, signal, ch, min_limit, max_limit, min_ref, max_ref,
                      param_code, param_str, samples, set_point):

        self.get_offsets_settings()
        param_value = self.dev_offsets[param_str]
        print('Initial value of parameter: ' + param_str + ' =', param_value)

        self.initiate_signals()

        # check if changing parameter value increase or decrease signal

        statistics_data = self.signals_statistics(samples)

        avg1 = float(statistics_data[signal + ch][0])

        self.rxtx('ns' + param_code + '=' + str(param_value + 500) + '|')

        statistics_data = self.signals_statistics(samples)

        avg2 = float(statistics_data[signal + ch][0])

        self.rxtx('ns' + param_code + '=' + str(param_value) + '|')

        if avg1 > avg2:
            flag = 1
            print('Signal value decreases with parameter')
        else:
            flag = 0
            print('Signal value increases with parameter')

        # end of check

        statistics_data = self.signals_statistics(samples)

        signal_average = float(statistics_data[signal + ch][0])
        print('Signal value = ', signal_average)
        counter = 0

        while ((signal_average < min_ref) or (signal_average > max_ref)) & (counter < 15):

            counter += 1
            print('\nRun # = ', counter)

            if signal_average < min_ref:
                if flag == 1:
                    max_limit = param_value
                    param_value = (min_limit + param_value) / 2
                else:
                    min_limit = param_value
                    param_value = (max_limit + param_value) / 2
                self.rxtx('ns' + param_code + '=' + str(param_value) + '|')

            elif signal_average > max_ref:
                if flag == 1:
                    min_limit = param_value
                    param_value = (max_limit + param_value) / 2
                else:
                    max_limit = param_value
                    param_value = (min_limit + param_value) / 2
                self.rxtx('ns' + param_code + '=' + str(param_value) + '|')

            time.sleep(0.2)

            statistics_data = self.signals_statistics(samples)

            signal_average = float(statistics_data[signal + ch][0])

            print('param_value = ', param_value)
            print('min lim = ', min_limit)
            print('max lim = ', max_limit)
            print('\nSignal value = ', signal_average)

        # optimize parameter value by searching around SP +/- N
        diffs = []
        averages = []
        N = 2
        param_values = list(np.linspace(param_value - N, param_value + N, 2*N + 1))

        for i in param_values:
            self.rxtx('ns' + param_code + '=' + str(i) + '|')
            time.sleep(0.2)
            statistics_data = self.signals_statistics(2 * samples)
            averages.append(float(statistics_data[signal + ch][0]))
            diffs.append(np.abs(float(statistics_data[signal + ch][0]) - set_point))

        print(diffs)
        signal_average = averages[diffs.index(np.min(diffs))]
        self.rxtx('ns' + param_code + '=' + str(param_values[diffs.index(np.min(diffs))]) + '|')

        print('\nFinal - ' + signal + ch + ' = ' + str(signal_average) + '\n')
