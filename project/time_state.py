_time_scale = 1.0
_time_ms = 0


def set_time_state(time_scale, time_ms):
    global _time_scale, _time_ms
    _time_scale = time_scale
    _time_ms = time_ms


def get_time_scale():
    return _time_scale


def get_time_ms():
    return _time_ms
