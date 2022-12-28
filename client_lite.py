import json
import sys
from selectors import DefaultSelector, EVENT_READ
from socket import socket
from threading import Thread


class Client:
    def __init__(self, host='127.0.0.1', port=1717):
        self.client_socket = socket(2, 1)
        self.client_socket.connect((host, port))

    def run(self):
        sls = DefaultSelector()

        def fun():
            while True:
                try:
                    data = sys.stdin.readline()
                    # sys.stdin.flush()
                except:
                    self.client_socket.close()
                    sys.exit()

                try:
                    self.client_socket.send(data.encode())
                except:
                    self.client_socket.close()
                    sls.close()
                    sys.exit()

                if data.startswith('quit'):
                    self.client_socket.close()
                    sys.exit()

        sls.register(self.client_socket, EVENT_READ)
        Thread(target=fun).start()
        while True:
            try:
                events = sls.select()
            except:
                self.client_socket.close()
                sys.exit()
            for _, mask in events:
                try:
                    msg = self.client_socket.recv(1000).decode('gbk')
                    if len(msg) == 0:
                        raise Exception()
                    sys.stdout.write(msg)
                    sys.stdout.flush()
                except:
                    self.client_socket.close()
                    sys.exit()


if __name__ == '__main__':
    default_config = {
        'host': '127.0.0.1',
        'port': 1717,
    }
    try:
        with open('client.json', 'r') as f:
            file_config = json.load(f)
    except:
        file_config = {}
    default_config.update(file_config)
    try:
        with open('client.json', 'w') as f:
            json.dump(default_config, f)
    except:
        pass
    c = Client(default_config['host'], default_config['port'])
    c.run()
