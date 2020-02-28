from funcy import memoize

import state.action_types as at
from state.store import store


def _reselect(selector, action_filter):

    def reselector():
        if action_filter():
            selector.memory.clear()

    store.subscribe(reselector)

    return selector


def last_action():
    """Get the last action from the store"""
    return store.get_state()['last_action']


@memoize
def _link_configuration():
    """Get the links configuration from the store"""
    return store.get_state()['link_configuration']

link_configuration = _reselect(_link_configuration, lambda: last_action() == at.UPDATE_LINK_CONFIGURATION)


@memoize
def _links():
    """Get the links from the store"""
    return store.get_state()['links']

links = _reselect(_links, lambda: last_action() == at.UPDATE_LINKS)


@memoize
def _bail_event():
    """Get the bail event from the store"""
    return store.get_state()['bail_event']

bail_event = _reselect(_bail_event, lambda: last_action() == at.UPDATE_BAIL_EVENT)
