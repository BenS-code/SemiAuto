from socket import *
import struct
import numpy as np
import time


class NTM:

    def __init__(self, communication, com_port, sn, ip, port):

        self.dev_data = {'dev_type': None, 'single_dual': None, 'hw': None, 'fw': None, 'update_rate': None,
                         'cycle_time': None, 'update_rate_code': None}

        self.dev_gains_conf = {'gain_ch1': None, 'gain_ch2': None, 'is_scale_ch1': None, 'is_scale_ch2': None,
                               'integrator_mode': None, 'is_integrator_mode': None, 'max_gain': None}

        self.dev_lph_conf = {'lph_ch1': None, 'lph_ch1_scale': None, 'lph_ch2': None, 'lph_ch2_scale': None,
                             'max_lph_ch1': None, 'max_lph_ch1_scale': None, 'max_lph_ch2': None,
                             'max_lph_ch2_scale': None, 'is_lph_sync': None}

        self.dev_offsets = {'offset_in_IL': None, 'offset_in_IS': None, 'offset_in_RC': None, 'offset_rf_IL': None,
                            'offset_rf_IS': None, 'offset_a2d_emission_IL': None, 'offset_a2d_emissivity_IL': None,
                            'offset_a2d_emission_IS': None, 'offset_rf_RC': None, 'offset_a2d_emission_RC': None,
                            'offset_a2d_emissivity_RC': None, 'offset_in_ch1': None, 'offset_in_ch2': None,
                            'offset_in_scale_ch1': None, 'offset_rf_ch1': None, 'offset_in_scale_ch2': None,
                            'offset_rf_ch2': None, 'offset_a2d_emission_ch1': None, 'offset_a2d_emissivity_ch1': None,
                            'offset_a2d_emission_ch2': None, 'offset_a2d_emissivity_ch2': None}

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
            try:
                [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)
                if command == 'dts':
                    while not (data == b'DTOK\n' or data == b'DTErr\n'):
                        [data, _] = self.udp_client_socket.recvfrom(self.buffer_size)

                print(self.sn + ' - sent data:', command)
                print(self.sn + ' - received data:', data)

                split_data = data.decode('ISO-8859-1').split('|')
                split_data = split_data[:-1]
                try:
                    for i in split_data:
                        results.append(i.split('=')[1])

                except IndexError:
                    print('Problem occurred in data received')

                return results
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
            try:
                data = self.com_port.readline()

                split_data = data.decode('ISO-8859-1').split('|')
                for i in split_data[:-1]:
                    results.append(i.split('=')[1])

                # print('sent data:', command)
                # print('received data:', data)
                return results

            except error:

                print("Could not connect with the serial-port")
                data = "Error"
                return data

    def get_device_data(self):
        data = self.rxtx('nr301|1001|106|1126|1120|101|')
        update_rate_code = data[0]
        cycle_time = data[1]
        update_rate = round(1 / ((10 ** -6) * int(update_rate_code) * int(cycle_time)), 2)
        dev_type = data[2]
        single_dual = data[3]
        hw = data[4]
        fw = data[5]

        if int(hw) == 1:
            hw = 'Integrator'
        elif int(hw) == 0:
            hw = 'Standard'

        if int(single_dual) == 1:
            single_dual = 'Dual'
        elif int(single_dual) == 0:
            single_dual = 'Single'

        self.dev_data['dev_type'] = dev_type
        self.dev_data['single_dual'] = single_dual
        self.dev_data['hw'] = hw
        self.dev_data['fw'] = fw
        self.dev_data['update_rate'] = update_rate
        self.dev_data['cycle_time'] = cycle_time
        self.dev_data['update_rate_code'] = update_rate_code

    def get_gain_settings(self):

        data = self.rxtx('nr501|508|510|516|1201|1120|561|')

        self.dev_gains_conf['gain_ch1'] = data[0]
        self.dev_gains_conf['gain_ch2'] = data[1]
        self.dev_gains_conf['is_scale_ch1'] = data[2]
        self.dev_gains_conf['is_scale_ch2'] = data[3]
        self.dev_gains_conf['integrator_mode'] = data[4]
        self.dev_gains_conf['is_integrator_mode'] = data[5]

        try:
            self.dev_gains_conf['max_gain'] = data[6]
        except IndexError:
            print('Max gain (code 561) is not defined in this fw - return default 8000')
            self.dev_gains_conf['max_gain'] = 8000

    def get_lph_settings(self):

        data = self.rxtx('nr2030|2031|2130|2131|2170|2171|2172|2173|2083|')

        self.dev_lph_conf['lph_ch1'] = data[0]
        self.dev_lph_conf['lph_ch1_scale'] = data[1]
        self.dev_lph_conf['lph_ch2'] = data[2]
        self.dev_lph_conf['lph_ch2_scale'] = data[3]
        self.dev_lph_conf['max_lph_ch1'] = data[4]
        self.dev_lph_conf['max_lph_ch1_scale'] = data[5]
        self.dev_lph_conf['max_lph_ch2'] = data[6]
        self.dev_lph_conf['max_lph_ch2_scale'] = data[7]
        self.dev_lph_conf['is_lph_sync'] = data[8]

    def get_offsets_settings(self):
        data = self.rxtx('nr2035|2036|2041|2040|2047|2046|2037|2038|2039|2138|1211|1221|1222|')

        if self.dev_gains_conf['is_integrator_mode'] == 1:
            self.dev_offsets['offset_in_IL'] = float(data[0])
            self.dev_offsets['offset_in_IS'] = float(data[1])
            self.dev_offsets['offset_in_RC'] = float(data[2])
            self.dev_offsets['offset_rf_IL'] = float(data[3])
            self.dev_offsets['offset_rf_IS'] = float(data[5])
            self.dev_offsets['offset_a2d_emission_IL'] = float(data[6])
            self.dev_offsets['offset_a2d_emissivity_IL'] = float(data[7])
            self.dev_offsets['offset_a2d_emission_IS'] = float(data[8])
            self.dev_offsets['offset_rf_RC'] = float(data[10])
            self.dev_offsets['offset_a2d_emission_RC'] = float(data[11])
            self.dev_offsets['offset_a2d_emissivity_RC'] = float(data[12])

        else:
            self.dev_offsets['offset_in_ch1'] = float(data[0])
            self.dev_offsets['offset_in_ch2'] = float(data[1])
            self.dev_offsets['offset_in_scale_ch1'] = float(data[2])
            self.dev_offsets['offset_rf_ch1'] = float(data[3])
            self.dev_offsets['offset_in_scale_ch2'] = float(data[4])
            self.dev_offsets['offset_rf_ch2'] = float(data[5])
            self.dev_offsets['offset_a2d_emission_ch1'] = float(data[6])
            self.dev_offsets['offset_a2d_emissivity_ch1'] = float(data[7])
            self.dev_offsets['offset_a2d_emission_ch2'] = float(data[8])
            self.dev_offsets['offset_a2d_emissivity_ch2'] = float(data[9])

    def set_gain_settings(self, mode, gain_index):

        """
        standard HW:
        normal/scale => mode = 0/1

        Integrator HW:
        AGC/IL/IS/RC => mode = 0/1/2/3

         gain_index = index{[AGC, 1, 2, 4, 8, 10, 20, 40, 80, 100, 200, 400, 800, 1000, 2000, 4000, 8000]}
         index =............[.0.,.1,.2,.3,.4,.5.,.6.,.7.,.8.,.9..,.10.,.11.,.12.,..13.,..14.,..15.,..16.]
        """

        if self.dev_data['hw'] == 'Standard':
            code = '510'
        elif self.dev_data['hw'] == 'Integrator':
            code = '1201'
        else:
            code = '510'

        self.rxtx('ns' + code + '=' + str(mode) + '|501=' + str(gain_index) + '|')

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

    def binary_search(self, signal, ch, low, high, set_point, knob_parameter, samples):
        signal_arr = []

        self.initiate_signals()

        statistics_data = self.signals_statistics(samples)

        signal_average = float(statistics_data[signal + ch][0])

        # if set_point< signal_average

    def set_signal_value(self, signal, ch, min_limit, max_limit, gain, gain_mode, samples, set_point):

        # define parameter to modify
        if self.dev_data['hw'] == 'Standard':
            knob_params_dict = {'agc_emission_ch1_0_16': '2035', 'agc_emission_ch2_0_16': '2036',
                                'agc_emission_ch1_1_16': '2041', 'agc_emission_ch2_1_16': '2047',
                                'emission_ch1_0_1': '', 'emission_ch2_0_1': '',
                                'emission_ch1_0_16': '', 'emission_ch2_0_16': ''}

        elif self.dev_data['hw'] == 'Integrator':
            pass

        self.set_gain_settings(gain_mode, gain)

        time.sleep(1)

        self.initiate_signals()

        statistics_data = self.signals_statistics(samples)

        signal_average = float(statistics_data[signal + ch][0])
        signal_std = float(statistics_data[signal + ch][1])

        min_ref = set_point - (signal_std / 2)
        max_ref = set_point + (signal_std / 2)

        print('\nSignal: ', signal + ch)
        print('--------------------------')
        print('Average: ', signal_average)
        print('STD: ', signal_std)
        print('min ref: ', min_ref)
        print('max ref: ', max_ref)

        # self.binary_search(signal, ch, min_limit, max_limit, set_point, knob_parameter, samples)

        # while (signal_average < min_ref) or (signal_average > max_ref):
        #     pass
