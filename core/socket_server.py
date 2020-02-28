from select import select
from queue import Queue
import socket
import logging
import sys

import state.selectors as sel


log = logging.getLogger(__name__)


def tcp_socket_server(ip_address, ip_port):
    log.info(f'Starting socket server on {ip_address}:{ip_port}')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.bind((ip_address, ip_port))
    log.debug(f'Bound to socket: {ip_address}:{ip_port}')
    sock.listen(5)
    log.debug(f'Listening on {ip_address}:{ip_port}')
    return sock


def queue_multiplex(single_queue, queue_dict, drop=False):
    if queue_dict or drop:
        obj = single_queue.get()
        log.debug(f'Broadcast message: {obj}')
        for queue in queue_dict.values():
            queue.put(obj)


def serve(ip_address, ip_port, send_queue, recv_queue, drop=False):
    server = tcp_socket_server(ip_address, ip_port)
    sockets = [server]
    socket_queues = {}
    readable = []
    writeable = []
    exceptional = []

    def in_exception(sock):
        exceptional.append(sock)
        if sock in writeable:
            writeable.remove(sock)

    while sockets:
        if not send_queue.empty():
            queue_multiplex(send_queue, socket_queues, drop=drop)

        readable, writeable, exceptional = select(sockets, sockets, sockets)
        for sock in readable:
            if sock is server:
                conn, _ = sock.accept()
                log.info(f'Accepted client: {conn.getpeername()}')
                conn.setblocking(0)
                sockets.append(conn)
                socket_queues[conn] = Queue()
            else:
                try:
                    data = sock.recv(1024)
                except ConnectionResetError:
                    in_exception(sock)
                if data:
                    log.debug(f'Received from {sock.getpeername()}: {data}')
                    recv_queue.put(data)
                else:
                    in_exception(sock)

        for sock in writeable:
            if not socket_queues[sock].empty():
                msg = socket_queues[sock].get()
                sock.send(msg)
                log.debug(f'Sent to {sock.getpeername()}: {msg}')

        for sock in exceptional:
            log.info(f'Dropping client: {sock.getpeername()}')
            sockets.remove(sock)
            sock.close()
            del socket_queues[sock]


if __name__ == "__main__":
    ip = 'localhost'
    port = 9000
    loopback = Queue()

    logging.basicConfig(level=logging.DEBUG)

    try:
        serve(ip, port, loopback, loopback)
    except KeyboardInterrupt:
        pass
