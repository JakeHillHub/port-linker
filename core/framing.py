SLIP_FRAME_END = 0x61
def is_full_slip_frame(data):
    return data[0] == SLIP_FRAME_END and data[-1] == SLIP_FRAME_END and len(data) > 1


def no_framing(_):
    return True


def factory(framing):
    return {
        'none': no_framing,
        'slip': is_full_slip_frame
    }[framing]
