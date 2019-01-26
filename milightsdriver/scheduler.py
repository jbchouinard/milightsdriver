import argparse
import datetime
import logging
import time
from collections import namedtuple

from milightsdriver import milight
from milightsdriver.milight import Off
from milightsdriver.colors import *


schedule = {
    '0:00-6:45': Off(),
    '6:45-7:30': [WARM_WHITE._replace(brightness=0), WARM_WHITE],
    '7:30-10:00': [WARM_WHITE, WARM_WHITE.mix(COOL_WHITE)],
    '10:00-19:00': WARM_WHITE.mix(COOL_WHITE),
    '19:00-21:00': [WARM_WHITE.mix(COOL_WHITE), WARM_WHITE],
    '21:00-22:00': [C_WARM_WHITE, RED._replace(brightness=70)],
    '22:00-23:15': [RED._replace(brightness=70), RED._replace(brightness=0)],
    '23:15-23:59': Off(),
}


def parse_time(time: str) -> datetime.time:
    return datetime.datetime.strptime(time, '%H:%M').time()

def now():
    return datetime.datetime.now().time()


def minute_of_day(time: datetime.time) -> int:
    return time.hour * 60 + time.minute


class Scheduler:
    Period = namedtuple('Period', ['start_time', 'end_time', 'mode1', 'mode2'])

    def __init__(self, controller, schedule, delay=10):
        self.controller = controller
        self.schedule = self.parse_schedule(schedule)
        self.mode = None
        self.delay = delay

    def run(self):
        while True:
            time_now = now()
            self.mode = self.get_mode_at(time_now)
            if self.mode is not None:
                logging.debug('Setting mode to {!r}'.format(self.mode))
                self.controller.set_all(self.mode)
                self.controller.set_all(self.mode)
            time.sleep(self.delay)

    def period_progress(self, period, at_time):
        start = minute_of_day(period.start_time)
        end = minute_of_day(period.end_time)
        at = minute_of_day(at_time)
        return (at - start) / (end - start)

    def get_mode_at(self, time: datetime.time):
        for period in self.schedule:
            if time >= period.start_time and time <= period.end_time:
                if period.mode2 is None:
                    return period.mode1
                return period.mode1.mix(period.mode2, ratio=self.period_progress(period, time))

    def parse_schedule(self, schedule):
        sched = []
        for times, mode_or_modes in schedule.items():
            start, end = [parse_time(t) for t in times.split('-')]
            if isinstance(mode_or_modes, list):
                mode1, mode2 = mode_or_modes
            else:
                mode1 = mode_or_modes
                mode2 = None
            sched.append(self.Period(start, end, mode1, mode2))
        return sorted(sched, key=lambda s: s.start_time)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--log-level', default='INFO')
    args = parser.parse_args()
    log_level = logging.getLevelName(args.log_level.upper())
    logging.basicConfig(level=log_level, format='%(asctime)s | %(levelname)s | %(message)s')
    logging.info('Trying to connect to milights-rest at {!r}'.format(args.url))
    client = milight.Client(args.url)
    controller = milight.Controller(client)
    logging.info('Starting')
    scheduler = Scheduler(controller, schedule)
    scheduler.run()


if __name__ == '__main__':
    main()