import sys
import threading
from queue import Queue, Empty

import serial

import state.selectors as sel
from core.socket_server import serve
from core.framing import factory as detect_frame_factory

def print_flush(print_str):
    print(print_str)
    sys.stdout.flush()


def serial_link(link, rx_queue, tx_queue, detect_frame):
    port = link['address']
    baud = link['baud']
    timeout = link['timeout']

    rx_buffer = bytearray()
    tx_buffer = bytearray()

    with serial.Serial(port, baud, timeout=timeout) as sser:
        print_flush('Opened Serial Port {}:{}:{}:{}'.format(link['id'], port, baud, timeout))

        def tx():
            while not sel.bail_event().is_set():
                try:
                    tx_data = rx_queue.get(timeout=timeout)
                    tx_buffer.extend(tx_data)
                    if detect_frame(tx_buffer):
                        sser.write(bytes(tx_buffer))
                        tx_buffer.clear()
                except Empty:
                    pass

        def rx():
            while not sel.bail_event().is_set():
                rx_data = sser.read()
                if rx_data:
                    rx_buffer.extend(rx_data)
                    if detect_frame(rx_buffer):
                        tx_queue.put(bytes(rx_buffer))
                        rx_buffer.clear()

        tx_thread = threading.Thread(target=tx)
        rx_thread = threading.Thread(target=rx)
        tx_thread.start()
        rx_thread.start()
        tx_thread.join()
        rx_thread.join()

    print_flush('Closed {}:{}:{}:{}'.format(link['id'], port, baud, timeout))


def tcp_listen_link(link, rx_queue, tx_queue, detect_frame):
    address = link['address']
    port = link['port']
    timeout = link['timeout']

    tcp_send_queue = Queue()
    tcp_recv_queue = Queue()

    rx_buffer = bytearray()
    tx_buffer = bytearray()

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
                tx_buffer.extend(tx_data)
                if detect_frame(tx_buffer):
                    tcp_send_queue.put(bytes(tx_buffer))
                    tx_buffer.clear()
            except Empty:
                pass

    def rx():
        while not sel.bail_event().is_set():
            try:
                rx_data = tcp_recv_queue.get(timeout=timeout)
                rx_buffer.extend(rx_data)
                if detect_frame(rx_buffer):
                    tx_queue.put(rx_data)
                    rx_buffer.clear()
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
    framing = link_def['framing']
    link1 = link_def['links'][0]
    link2 = link_def['links'][1]

    print_flush('Linking {} to {}'.format(link1, link2))

    rx_queue = Queue()
    tx_queue = Queue()

    link_type_map = {
        'tcp-listener': tcp_listen_link,
        'serial': serial_link
    }

    detect_frame = detect_frame_factory(framing)

    link1_t = threading.Thread(target=link_type_map[link1['type']], args=(link1, rx_queue, tx_queue, detect_frame))
    link2_t = threading.Thread(target=link_type_map[link2['type']], args=(link2, tx_queue, rx_queue, detect_frame))

    return {
        'name': link_name,
        'threads': (link1_t, link2_t)
    }
