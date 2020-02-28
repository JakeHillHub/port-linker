def update_link_configuration(state, action):
    """Update link configuration"""

    return {
        **state,
        'link_configuration': action['link_configuration']
    }


def update_bail_event(state, action):
    """Update bail event"""
    
    return {
        **state,
        'bail_event': action['bail_event']
    }


def update_links(state, action):
    """Update the existing links"""

    return {
        **state,
        'links': state['links'] + [action['link']]
    }
