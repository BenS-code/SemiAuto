from socket import *
import serial
import serial.tools.list_ports


class LAN:

    def __init__(self, port, time_out, data):
        self.port = port
        self.time_out = time_out
        self.data = data
        self.s = socket(family=AF_INET, type=SOCK_DGRAM)
        self.s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.s.settimeout(self.time_out)

        self.find_device()

    def find_device(self):
        sn_list = []
        ip_list = []
        lan_list = []
        self.s.sendto(self.data, ('<broadcast>', self.port))

        while True:

            try:
                [data, address] = self.s.recvfrom(1024)
                data = data.decode()
                start = int(data.find('102=')) + 4
                end = start + int(data[(data.find('102=') + 4):].find('|'))
                sn = data[start:end]
                ip = address[0]

                if sn not in sn_list:
                    sn_list.append(sn)
                    ip_list.append(ip)

            except timeout:
                for i in range(0, len(sn_list)):
                    lan_list.append(str(sn_list[i]) + ', ' + str(ip_list[i]))

                break

        return lan_list, sn_list, ip_list


class RS232:

    def __init__(self):
        self.port = None
        self.ports = None
        self.s = None

    def show_ports(self):
        # function lists COM ports in combobox

        self.ports = serial.tools.list_ports.comports(include_links=False)
        com_ports = []
        for i in sorted(self.ports):
            com_ports.append(i.device)

        return com_ports

    def connect_serial(self, port):
        # function connects NTM to COM port
        self.port = port

        try:
            # define serial port
            self.s = serial.Serial(
                port=self.port,
                baudrate=115200,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1)

            return self.s

        except serial.SerialException:
            print("Access is denied")


