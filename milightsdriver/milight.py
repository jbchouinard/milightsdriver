import time
from collections import namedtuple
from typing import Union, Iterable, Optional

import requests


DEFAULT_URL = "http://localhost"


class Client:
    def __init__(self, root_url: str = DEFAULT_URL):
        self.root_url = root_url.strip("/")

    def __repr__(self):
        return "Client({!r})".format(self.root_url)

    def url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            return path_or_url
        return "/".join([self.root_url, "api", path_or_url.strip("/")])

    def get(self, path_or_url: str):
        resp = requests.get(self.url(path_or_url))
        resp.raise_for_status()
        parsed = resp.json()
        assert parsed["status"] == 200
        return parsed["data"]

    def put(self, path_or_url, data):
        resp = requests.put(self.url(path_or_url), json=data)
        resp.raise_for_status()
        parsed = resp.json()
        assert parsed["status"] == 200
        return parsed["data"]

    def get_zone(self, name):
        return self.get("/zones/{}".format(name))

    def put_zone(self, name, mode, state=None):
        if state is None:
            state = {}
        return self.put("/zones/{}".format(name), data={"mode": mode, "state": state})

    def get_zones(self):
        return self.get("/zones")

    def put_zones(self, mode, state):
        return self.put("/zones", data={"mode": mode, "state": state})


class Off(namedtuple("OffBase", [])):
    name = "off"


class Night(namedtuple("NightBase", [])):
    name = "night"


class Color(namedtuple("ColorBase", ["hue", "brightness", "saturation"])):
    name = "color"

    @staticmethod
    def mix_hues(hue1, hue2, ratio=0.5):
        diff = hue2 - hue1
        if diff > 127:
            diff -= 256
        if diff < -127:
            diff += 256
        return (hue1 + round(diff * ratio)) % 256

    def mix(self, other: "Color", ratio: float = 0.5) -> "Color":
        ratio = min(1, max(0, ratio))
        return Color(
            self.mix_hues(self.hue, other.hue, ratio),
            round(self.brightness * (1 - ratio) + other.brightness * ratio),
            round(self.saturation * (1 - ratio) + other.saturation * ratio),
        )


class White(namedtuple("WhiteBase", ["temperature", "brightness"])):
    name = "white"

    def mix(self, other: "White", ratio: float = 0.5) -> "White":
        ratio = min(1, max(0, ratio))
        return White(
            round(self.temperature * (1 - ratio) + other.temperature * ratio),
            round(self.brightness * (1 - ratio) + other.brightness * ratio),
        )


class Effect(
    namedtuple("EffectBase", ["effect_mode", "brightness", "saturation", "speed"])
):
    name = "effect"


Mode = Union[Off, Night, Color, White, Effect]

modes = {m.name: m for m in [Off, Night, Color, White, Effect]}


def state(mode: Mode) -> dict:
    return dict(mode._asdict())


def mode(mode_name: str, state: dict) -> Mode:
    return modes[mode_name](**state)


class Zone:
    def __init__(self, client, name, data=None):
        if data is None:
            data = client.get_zone(name)
        self.client = client
        self.name = name
        self._mode = mode(data["mode"], data["state"])

    def __repr__(self):
        return "Zone({!r}, {!r})".format(self.client, self.name)

    @property
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, value: Mode):
        self._mode = value
        self.push()

    def push(self):
        self.data = self.client.put_zone(
            name=self.name, mode=self.mode.name, state=state(self.mode)
        )


class Controller:
    def __init__(self, client: Client, autoload=True):
        self.client = client
        self.zones = {}
        if autoload:
            self.add_all()

    def __repr__(self):
        return "Controller({!r})".format(self.client)

    def add(self, name, data=None):
        self.zones[name] = Zone(self.client, name, data)

    def add_all(self):
        zones_data = self.client.get_zones()
        for data in zones_data:
            self.add(data["name"], data)

    def set_all(self, mode: Mode):
        for zone in self.zones.values():
            zone.mode = mode

    def set(self, name, mode: Mode):
        self.zone(name).mode = mode

    def zone(self, name):
        return self.zones[name]

    def animate(
        self,
        modes: Iterable[Mode],
        delay: int = 0,
        zones: Optional[Iterable[Zone]] = None,
    ):
        if zones is None:
            zones = self.zones.values()
        for mode in modes:
            for zone in zones:
                zone.mode = mode
            time.sleep(delay)


def test_client():
    client = Client()
    zones = client.get_zones()
    assert zones
    zone_by_name = client.get_zone(zones[0]["name"])
    zone_by_link = client.get(zones[0]["link"])
    assert zone_by_name == zone_by_link
    print("test_client ok.")


if __name__ == "__main__":
    test_client()
