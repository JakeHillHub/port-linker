import argparse
import threading
import signal
import serial
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--master', dest='master', type=str, required=True, help='Master Serial Device')
    parser.add_argument('-s', '--slave', dest='slave', type=str, required=True, help='Slave Serial Device')
    parser.add_argument('-b', '--baud', dest='baud', default=115200, type=int, help='Device baudrate default 115200')
    parser.add_argument('-t', '--timeout', dest='timeout', default=1, type=int, help='Serial port timeout default 1 second')
    parsed_args = parser.parse_args()

    s_thread = threading.Thread(target=run_slave, args=(parsed_args.slave, parsed_args.baud, parsed_args.timeout))
    m_thread = threading.Thread(target=run_master, args=(parsed_args.master, parsed_args.baud, parsed_args.timeout))

    signal.signal(signal.SIGINT, lambda _,__: bail_event.set())

    s_thread.start()
    m_thread.start()
    s_thread.join()
    m_thread.join()
