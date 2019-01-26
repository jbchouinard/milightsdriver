import re

from milightsdriver.milight import Color, White

RED = Color(0, 100, 0)
GREEN = Color(85, 100, 0)
BLUE = Color(170, 100, 0)
CYAN = BLUE.mix(GREEN)
MAGENTA = BLUE.mix(RED)
YELLOW = RED.mix(GREEN)
ORANGE = RED.mix(YELLOW)

WHITE = White(50, 100)
WARM_WHITE = White(0, 100)
C_WARM_WHITE = Color(25, 100, 100)
COOL_WHITE = White(100, 100)
C_COOL_WHITE = Color(145, 100, 100)

COLORS = {
    'red': RED,
    'green': GREEN,
    'blue': BLUE,
    'cyan': CYAN,
    'magenta': MAGENTA,
    'yellow': YELLOW,
    'orange': ORANGE,
    'white': WHITE,
    'warm white': WARM_WHITE,
    'cool white': COOL_WHITE
}

re_color = re.compile(r'(?P<sat_mod>pale)? ?(?P<br_mod>bright|dark)? ?(?P<color>[a-z ]+)')

def color_by_name(name):
    m = re_color.match(name)
    if not m:
        raise ValueError("{} unexpected format for color name")
    col = COLORS[m.group('color')]
    mod = m.group('br_mod')
    if mod == 'bright':
        col = col._replace(brightness=100)
    elif mod == 'dark':
        col = col._replace(brightness=33)
    else:
        col = col._replace(brightness=66)
    if m.group('sat_mod'):
        col = col._replace(saturation=50)
    return col

