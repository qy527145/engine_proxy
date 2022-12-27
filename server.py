import json
import logging.handlers
import socket
from selectors import DefaultSelector, EVENT_READ
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

from commandline_config import Config

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
s_handle = logging.StreamHandler()
s_handle.setLevel(logging.INFO)
s_handle.setFormatter(formatter)
f_handle = logging.handlers.TimedRotatingFileHandler(filename='engine.log')
f_handle.setLevel(logging.INFO)
f_handle.setFormatter(formatter)
logger.addHandler(s_handle)
logger.addHandler(f_handle)
logger.setLevel(logging.DEBUG)


def keepalive(sock: socket.socket):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 2)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
    # sock.ioctl(socket.SIO_KEEPALIVE_VALS, (2, 1, 3))
    return sock


class Engine:
    def __init__(self, path: str, callback=None, callback_args=None, callback_kwargs=None, ):
        if callback is None:
            callback = print
            callback_kwargs = {'end': ''}
        if callback_args is None:
            callback_args = ()
        if callback_kwargs is None:
            callback_kwargs = {}
        self.proc = Popen(path, stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True)
        self.callback = callback
        self.args = callback_args
        self.kwargs = callback_kwargs
        self.closed = False
        self.recv_thread = Thread(target=self.auto_recv)
        self.recv_thread.start()

    def auto_recv(self):
        while not self.closed:
            try:
                self.callback(self.proc.stdout.readline(), *self.args, **self.kwargs)
            except:
                self.close()

    def send(self, cmd):
        self.proc.stdin.write(cmd)
        self.proc.stdin.flush()

    def close(self):
        if not self.closed:
            self.closed = True
            self.proc.stdin.close()
            self.proc.stdout.close()
            self.proc.kill()


class Server:
    def __init__(self, host='127.0.0.1', port=1717, engine_path=None):
        self.server_socket = keepalive(socket.socket(2, 1))
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.engine_path = engine_path
        self.pool = {}

    def run(self):
        logger.info('服务正在启动...')
        sls = DefaultSelector()

        def send(msg, conn):
            try:
                conn.send(msg.encode('gbk'))
            except:
                logger.info(f'客户端<{self.pool.pop(conn)[0]}>已断开连接，正在关闭对应引擎...')
                sls.unregister(conn)
                conn.close()
                raise Exception()

        def accept():
            conn, addr = self.server_socket.accept()
            logger.info(f'收到来自<{addr}>的连接请求')
            engine = Engine(path=self.engine_path, callback=send, callback_args=(conn,))
            logger.info(f'已为客户端<{addr}>启动引擎')
            sls.register(conn, EVENT_READ)
            self.pool[conn] = (addr, engine)

        sls.register(self.server_socket, EVENT_READ, accept)

        logger.info('正在监听客户端连接...')
        while True:
            for key, _ in sls.select():
                if key.fileobj == self.server_socket:
                    key.data()
                else:
                    try:
                        cmd = key.fileobj.recv(100).decode()
                        if len(cmd) == 0:
                            raise Exception()
                        self.pool[key.fileobj][1].send(cmd)
                    except:
                        addr, engine = self.pool.pop(key.fileobj)
                        logger.info(f'客户端<{addr}>已断开连接，正在关闭对应引擎...')
                        sls.unregister(key.fileobj)
                        key.fileobj.close()
                        engine.close()


if __name__ == '__main__':
    default_config = {
        'path': '',
        'host': '0.0.0.0',
        'port': 1717,
    }
    try:
        with open('server.json', 'r') as f:
            file_config = json.load(f)
    except:
        file_config = {}
    default_config.update(file_config)
    helpers = {
        'path': '引擎路径',
        'host': '服务主机',
        'port': '服务端口',
    }
    config = Config(default_config, name='server', helpers=helpers, show=False)
    while not config.path:
        import sys

        if sys.platform.startswith('win'):
            import tkinter.filedialog

            config.path = tkinter.filedialog.askopenfilename()
            # assert config.path
        else:
            # raise Exception('引擎路径未指定')
            config.path = input('引擎路径：')

    config.save()
    s = Server(engine_path=config.path, host=config.host, port=config.port)
    s.run()
