import argparse
import threading
import signal
import serial
import socket
import time
import json
import sys

from pathlib import PurePath
from queue import Queue, Empty

import state.action_types as at
import state.selectors as sel
from state.store import store
from core.link import create_link


def load_config(config_path):
    with open(PurePath(config_path), 'r') as config_file:
        return json.loads(config_file.read())


def initialize_store(config):
    """Populate all initial store values"""

    store.dispatch({
        'type': at.UPDATE_LINK_CONFIGURATION,
        'link_configuration': config
    })
    store.dispatch({
        'type': at.UPDATE_BAIL_EVENT,
        'bail_event': threading.Event()
    })

    for link_name, link_conf in sel.link_configuration().items():
        store.dispatch({
            'type': at.UPDATE_LINKS,
            'link': create_link(link_name, link_conf)
        })


def start_links():
    for link in sel.links():
        threads = link['threads']
        for thread in threads:
            thread.start()


def await_links():
    for link in sel.links():
        threads = link['threads']
        for thread in threads:
            thread.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help='Serial link configuration json file')
    parser.add_argument('--wait', dest='wait', default=0, type=int, help='Wait for this many seconds to attempt to connect (hack for systemd)')
    parsed_args = parser.parse_args()

    config = load_config(parsed_args.config)
    initialize_store(config)

    time.sleep(parsed_args.wait)

    signal.signal(signal.SIGINT, lambda _,__: sel.bail_event().set())

    start_links()
    await_links()


if __name__ == '__main__':
    main()
