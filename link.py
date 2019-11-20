import argparse
import threading
import signal
import serial
import json

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


def run_slave(slave, baud, timeout):
    with serial.Serial(slave, baud, timeout=timeout) as sser:
        print('Opened {}:{}:{}'.format(slave, baud, timeout))

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


def run_master(master, baud, timeout):
    with serial.Serial(master, baud, timeout=timeout) as mser:
        print('Opened {}:{}:{}'.format(master, baud, timeout))

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


def load_config(config_path):
    with open(PurePath(config_path), 'r') as config_file:
        return json.loads(config_file.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help='Serial link configuration json file')
    parsed_args = parser.parse_args()

    config = load_config(parsed_args.config)

    threads = []
    for link in config:
        print('Linking {}:{}:{} to {}:{}:{}'.format(link['slave']['port'], link['slave']['baud'], link['slave']['timeout'],
                                                    link['master']['port'], link['master']['baud'], link['master']['timeout']))

        threads.append(threading.Thread(target=run_slave, args=(link['slave']['port'], link['slave']['baud'], link['slave']['timeout'])))
        threads.append(threading.Thread(target=run_slave, args=(link['master']['port'], link['master']['baud'], link['master']['timeout'])))

    signal.signal(signal.SIGINT, lambda _,__: bail_event.set())

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
