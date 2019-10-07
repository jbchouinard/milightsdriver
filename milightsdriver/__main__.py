import datetime
import logging

import click
import IPython

from .colors import color_by_name
from .milight import Client, Controller, Off, Night
from .scheduler import Scheduler, schedule


@click.group()
@click.option("--server", default="http://localhost")
@click.option("--log-level", default="INFO")
@click.pass_context
def cli(ctx, server, log_level):
    log_level = logging.getLevelName(log_level.upper())
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)s | %(message)s"
    )
    client = Client(server)
    ctl = Controller(client, autoload=True)
    ctx.obj = ctl


@cli.command()
@click.pass_context
def list(ctx):
    for name, zn in ctx.obj.zones.items():
        click.echo("{!s}: {!s} {}".format(name, zn.mode.name, dict(zn.mode._asdict())))


@cli.command()
@click.pass_context
def shell(ctx):
    from . import colors

    ctl = ctx.obj
    IPython.embed()


@cli.command()
@click.argument("zone")
@click.argument("mode")
@click.pass_context
def set(ctx, zone, mode):
    if mode == "off":
        m = Off()
    elif mode == "night":
        m = Night()
    else:
        m = color_by_name(mode)

    if zone == "all":
        ctx.obj.set_all(m)
    else:
        ctx.obj.zone(zone).mode = m


@cli.command()
@click.option("--pausefile", "-p", default=None)
@click.pass_context
def scheduler(ctx, pausefile):
    scheduler = Scheduler(ctx.obj, schedule, pausefile=pausefile)
    scheduler.run()


def parse_date(datestr):
    return datetime.datetime.strptime(datestr, "%Y-%m-%d").date()


def parse_time(timestr):
    return datetime.datetime.strptime(timestr, "%H:%M").time()


@cli.command()
@click.argument("time")
@click.option("-d", "--date", default=None)
@click.option("--interval", type=click.INT, default=3)
@click.pass_context
def schedule_test(ctx, time, date, interval):
    if date is None:
        date = datetime.date.today()
    else:
        date = parse_date(date)

    if "-" in time:
        start_time, end_time = time.split("-")
    else:
        start_time = end_time = time

    stime = datetime.datetime.combine(date, parse_time(start_time))
    etime = datetime.datetime.combine(date, parse_time(end_time))
    stime, etime = min(stime, etime), max(stime, etime)

    scheduler = Scheduler(ctx.obj, schedule)
    interval = datetime.timedelta(minutes=interval)
    while stime <= etime:
        click.echo(stime)
        scheduler.set_lights(stime)
        stime += interval


if __name__ == "__main__":
    cli()
