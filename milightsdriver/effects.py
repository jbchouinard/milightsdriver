from typing import Generator

from milightsdriver.milight import Color, Mode, White


Effect = Generator[Mode, None, None]


def steps(start: int, end: int, count: int) -> Effect:
    assert count >= 2
    inc = (end - start) / (count - 1)
    acc = start
    for _ in range(count):
        yield min(end, int(acc))
        acc += inc


def color_gradient(start_color: Color, end_color: Color, count: int) -> Effect:
    hues = steps(start_color.hue, end_color.hue, count)
    brs = steps(start_color.brightness, end_color.brightness, count)
    sats = steps(start_color.saturation, end_color.saturation, count)
    for hue, br, sat in zip(hues, brs, sats):
        yield Color(hue, br, sat)


def white_gradient(start_color: White, end_color: White, count: int) -> Effect:
    temps = steps(start_color.temperature, end_color.temperature, count)
    brs = steps(start_color.brightness, end_color.brightness, count)
    for temp, br, in zip(temps, brs):
        yield White(temp, br)


def sunrise(n: int = 100) -> Effect:
    return white_gradient(White(0, 0), White(100, 100), n)

