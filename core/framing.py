import re


SLIP_FRAME_END = 0xC0
slip_re = re.compile(b'.*?(\xC0.*?\xC0).*?')


def get_slip_frame(data):
    match = re.match(slip_re, data)
    if match:
        return match.group(1)
    return None


def no_framing(_):
    return True


def factory(framing):
    return {
        'none': no_framing,
        'slip': get_slip_frame
    }[framing]
