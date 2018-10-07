import argparse
import datetime
import logging
import time
from collections import namedtuple

from milightsdriver import milight
from milightsdriver.milight import Off
from milightsdriver.colors import *


schedule = {
    '0:00-1:00': RED._replace(brightness=0),
    '1:00-7:00': Off(),
    '7:00-9:00': [WARM_WHITE._replace(brightness=0), WARM_WHITE],
    '9:00-11:00': [WARM_WHITE, COOL_WHITE],
    '11:00-18:00': COOL_WHITE,
    '18:00-20:00': [COOL_WHITE, WARM_WHITE],
    '20:00-22:30': [C_WARM_WHITE, RED._replace(brightness=70)],
    '22:30-23:59': [RED._replace(brightness=70), RED._replace(brightness=0)],
}


def parse_time(time: str) -> datetime.time:
    return datetime.datetime.strptime(time, '%H:%M').time()

def now():
    return datetime.datetime.now().time()


def minute_of_day(time: datetime.time):
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
            mode = self.get_mode_at(time_now)
            if mode is not None and mode != self.mode:
                logging.debug('Changing mode to {!r}'.format(mode))
                self.controller.set_all(mode)
                self.mode = mode
            else:
                logging.debug('Mode unchanged')
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