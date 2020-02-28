import sys
import threading
from queue import Queue, Empty

import serial

import state.selectors as sel
from socket_server import serve


def print_flush(print_str):
    print(print_str)
    sys.stdout.flush()


def serial_link(link, rx_queue, tx_queue):
    port = link['address']
    baud = link['baud']
    timeout = link['timeout']

    with serial.Serial(port, baud, timeout=timeout) as sser:
        print_flush('Opened Serial Port {}:{}:{}:{}'.format(link['id'], port, baud, timeout))

        def tx():
            while not sel.bail_event().is_set():
                try:
                    tx_data = rx_queue.get(timeout=timeout)
                    sser.write(tx_data)
                except Empty:
                    pass

        def rx():
            while not sel.bail_event().is_set():
                rx_data = sser.read()
                if rx_data:
                    tx_queue.put(rx_data)

        tx_thread = threading.Thread(target=tx)
        rx_thread = threading.Thread(target=rx)
        tx_thread.start()
        rx_thread.start()
        tx_thread.join()
        rx_thread.join()

    print_flush('Closed {}:{}:{}:{}'.format(link['id'], port, baud, timeout))


def tcp_listen_link(link, rx_queue, tx_queue):
    address = link['address']
    port = link['port']
    timeout = link['timeout']

    tcp_send_queue = Queue()
    tcp_recv_queue = Queue()

    def _serve():
        try:
            serve(address, port, tcp_send_queue, tcp_recv_queue)
        except KeyboardInterrupt:
            pass

    threading.Thread(target=_serve).start()

    print_flush('TCP Listening On {}:{}:{}:{}'.format(link['id'], address, port, timeout))

    def tx():
        while not sel.bail_event().is_set():
            try:
                tx_data = rx_queue.get(timeout=timeout)
                tcp_send_queue.put(tx_data)
            except Empty:
                pass

    def rx():
        while not sel.bail_event().is_set():
            try:
                tx_data = tcp_recv_queue.get(timeout=timeout)
                tx_queue.put(tx_data)
            except Empty:
                pass

    tx_thread = threading.Thread(target=tx)
    rx_thread = threading.Thread(target=rx)
    tx_thread.start()
    rx_thread.start()
    tx_thread.join()
    rx_thread.join()

    print_flush('TCP Listening Stopped for {}:{}:{}:{}'.format(link['id'], address, port, timeout))


def create_link(link_name, link_def):
    link1 = link_def[0]
    link2 = link_def[1]

    print_flush('Linking {} to {}'.format(link1, link2))

    rx_queue = Queue()
    tx_queue = Queue()

    link_type_map = {
        'tcp-listener': tcp_listen_link,
        'serial': serial_link
    }

    link1_t = threading.Thread(target=link_type_map[link1['type']], args=(link1, rx_queue, tx_queue))
    link2_t = threading.Thread(target=link_type_map[link2['type']], args=(link2, tx_queue, rx_queue))

    return {
        'name': link_name,
        'threads': (link1_t, link2_t)
    }
