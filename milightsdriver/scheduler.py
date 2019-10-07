import datetime
import logging
import os
import time
from collections import namedtuple

from .milight import Mode, Off
from .colors import C_WARM_WHITE, WARM_WHITE, WHITE, ORANGE, RED


class Gradient:
    def __init__(self, mode1: Mode, mode2: Mode):
        self.mode1 = mode1
        self.mode2 = mode2

    def at(self, ratio):
        return self.mode1.mix(self.mode2, ratio=float(ratio))


O = "office"
K = "dining"
E = "entrance"


def OKE(mode):
    return {k: mode for k in (O, K, E)}


DUSK = ORANGE._replace(brightness=75)
DAY = WHITE
NIGHTLIGHT = RED._replace(brightness=25)
DO_NOTHING = None
OFF = Off()

SUNRISE_1 = Gradient(
    C_WARM_WHITE._replace(brightness=0), C_WARM_WHITE._replace(brightness=80)
)
SUNRISE_2 = Gradient(WARM_WHITE._replace(brightness=85), DAY)
SUNSET_0 = Gradient(DAY, WARM_WHITE._replace(brightness=85))
SUNSET_1 = Gradient(C_WARM_WHITE._replace(brightness=85), DUSK)
SUNSET_2 = Gradient(DUSK, DUSK.mix(NIGHTLIGHT, ratio=0.3))
SUNSET_3 = Gradient(DUSK.mix(NIGHTLIGHT, ratio=0.3), NIGHTLIGHT)
SUNSET = Gradient(C_WARM_WHITE, NIGHTLIGHT)


# fmt: off
early_morning = {
    "4:00-7:45": {O: OFF, K: OFF, E: NIGHTLIGHT},
    "7:45-8:30": OKE(SUNRISE_1),
    "8:30-09:00": OKE(SUNRISE_2),
    "8:30-20:00": OKE(DAY),
}

late_morning = {
    "4:00-10:45": {O: OFF, K: OFF, E: NIGHTLIGHT},
    "10:45-11:30": OKE(SUNRISE_1),
    "11:30-12:00": OKE(SUNRISE_2),
    "12:00-20:00": OKE(DAY),
}

early_night = {
    "20:00-21:30": OKE(SUNSET_0),
    "21:30-23:00": OKE(SUNSET_1),
    "23:00-23:59": OKE(SUNSET_2),
    "00:00-00:30": OKE(SUNSET_3),
    "00:30-04:00": {O: OFF, K: OFF, E: NIGHTLIGHT},
}

late_night = {
    "20:00-21:30": OKE(SUNSET_0),
    "21:30-23:00": OKE(SUNSET_1),
    "23:00-23:59": OKE(DO_NOTHING),
    "00:00-01:30": OKE(DO_NOTHING),
    "01:30-04:00": {O: OFF, K: OFF, E: NIGHTLIGHT},
}
# fmt: on
weekdays = dict(enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"], 1))


def combine(*schedules):
    sched = {}
    for s in schedules:
        sched.update(s)
    return sched


schedule = {
    "mon": combine(early_morning, early_night),
    "tue": combine(early_morning, early_night),
    "wed": combine(early_morning, early_night),
    "thu": combine(early_morning, early_night),
    "fri": combine(early_morning, late_night),
    "sat": combine(late_morning, late_night),
    "sun": combine(late_morning, early_night),
}


def get_mode(color, ratio):
    if isinstance(color, Gradient):
        return color.at(ratio)
    else:
        return color


def parse_time(time: str) -> datetime.time:
    return datetime.datetime.strptime(time, "%H:%M").time()


def minute_of_day(time: datetime.time) -> int:
    return time.hour * 60 + time.minute


class Scheduler:
    Period = namedtuple("Period", ["start_time", "end_time", "zones"])

    def __init__(self, controller, schedule, delay=3):
        self.controller = controller
        self.schedule = {k: self.parse_schedule(s) for k, s in schedule.items()}
        self.modes = {}
        self.delay = delay

    def run(self):
        while True:
            if not os.path.exists("/usr/home/jerome/deploy/milights-driver/paused"):
                self.set_lights(datetime.datetime.now())
            time.sleep(self.delay)

    def set_lights(self, now: datetime.datetime):
        # Pretend that midnight-4am belongs to previous day
        weekday = weekdays[(now - datetime.timedelta(hours=4)).isoweekday()]
        time = now.time()
        logging.debug("Using schedule for {} at {:%H:%M}".format(weekday.upper(), time))
        sched = self.schedule[weekday]
        self.modes = self.get_modes_at(sched, time)
        for zone, mode in self.modes.items():
            if mode is not None:
                logging.debug("Setting {!r} to {!r}".format(zone, mode))
                self.controller.set(zone, mode)

    def period_progress(self, period, at_time):
        start = minute_of_day(period.start_time)
        end = minute_of_day(period.end_time)
        at = minute_of_day(at_time)
        return (at - start) / (end - start)

    def get_modes_at(self, schedule, time: datetime.time):
        for period in schedule:
            if time >= period.start_time and time <= period.end_time:
                ratio = self.period_progress(period, time)
                modes = {}
                for name, color in period.zones.items():
                    modes[name] = get_mode(color, ratio)
                return modes

    def parse_schedule(self, schedule):
        sched = []
        for times, zones in schedule.items():
            start, end = [parse_time(t) for t in times.split("-")]
            sched.append(self.Period(start, end, zones))
        return sorted(sched, key=lambda s: s.start_time)
