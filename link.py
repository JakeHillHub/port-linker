import argparse
import threading
import signal
import serial
import json
import sys

from pathlib import PurePath
from queue import Queue, Empty

bail_event = threading.Event()


class Queues:

    _instance = None

    class _Queues:
        def __init__(self):
            self._queues = {
                'tx': Queue(),
                'rx': Queue()
            }

        @property
        def queues(self):
            return self._queues

    def __init__(self):
        if not Queues._instance:
            Queues._instance = Queues._Queues()

    @property
    def queues(self):
        return Queues._instance.queues


def print_flush(print_str):
    print(print_str)
    sys.stdout.flush()


def run_slave(slave, alias, baud, timeout):
    with serial.Serial(slave, baud, timeout=timeout) as sser:
        print_flush('Opened {}:{}:{}:{}'.format(alias, slave, baud, timeout))

        def tx():
            while not bail_event.is_set():
                try:
                    tx_data = Queues().queues['rx'].get(timeout=timeout)
                    sser.write(tx_data)
                except Empty:
                    pass

        def rx():
            while not bail_event.is_set():
                rx_data = sser.read()
                if rx_data:
                    Queues().queues['tx'].put(rx_data)

        tx_thread = threading.Thread(target=tx)
        rx_thread = threading.Thread(target=rx)
        tx_thread.start()
        rx_thread.start()
        tx_thread.join()
        rx_thread.join()

    print_flush('Closed {}:{}:{}:{}'.format(alias, slave, baud, timeout))


def run_master(master, alias, baud, timeout):
    with serial.Serial(master, baud, timeout=timeout) as mser:
        print_flush('Opened {}:{}:{}:{}'.format(alias, master, baud, timeout))

        def tx():
            while not bail_event.is_set():
                try:
                    tx_data = Queues().queues['tx'].get(timeout=timeout)
                    mser.write(tx_data)
                except Empty:
                    pass

        def rx():
            while not bail_event.is_set():
                rx_data = mser.read()
                if rx_data:
                    Queues().queues['rx'].put(rx_data)

        tx_thread = threading.Thread(target=tx)
        rx_thread = threading.Thread(target=rx)
        tx_thread.start()
        rx_thread.start()
        tx_thread.join()
        rx_thread.join()

    print_flush('Closed {}:{}:{}:{}'.format(alias, master, baud, timeout))


def load_config(config_path):
    with open(PurePath(config_path), 'r') as config_file:
        return json.loads(config_file.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help='Serial link configuration json file')
    parser.add_argument('alias_config', type=str, help='Alias configuration map')
    parsed_args = parser.parse_args()

    config = load_config(parsed_args.config)
    alias = load_config(parsed_args.alias_config)

    threads = []
    for link in config:
        slave_port = alias[link['slave']['port']]
        master_port = alias[link['master']['port']]
        print_flush('Linking {}:{}:{}:{} to {}:{}:{}:{}'.format(link['slave']['port'], slave_port, link['slave']['baud'], link['slave']['timeout'],
                                                          link['master']['port'], master_port, link['master']['baud'], link['master']['timeout']))

        threads.append(threading.Thread(target=run_slave, args=(slave_port, link['slave']['port'], link['slave']['baud'], link['slave']['timeout'])))
        threads.append(threading.Thread(target=run_master, args=(master_port, link['slave']['port'], link['master']['baud'], link['master']['timeout'])))

    signal.signal(signal.SIGINT, lambda _,__: bail_event.set())

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
