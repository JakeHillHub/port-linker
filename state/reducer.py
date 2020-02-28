import state.action_types as at
import state.actions as a


INITIAL_STATE = {
    'links': [],
    'link_configuration': {},
    'last_action': 'none',
    'bail_event': 'none'
}


def reducer(state, action):
    """pydux reducer"""

    if state is None:
        state = INITIAL_STATE

    state['last_action'] = action['type']

    return {
        at.UPDATE_LINK_CONFIGURATION: a.update_link_configuration,
        at.UPDATE_BAIL_EVENT: a.update_bail_event,
        at.UPDATE_LINKS: a.update_links
    }.get(action['type'], lambda state, action: state)(state, action)
