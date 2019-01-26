import click

from milightsdriver.colors import color_by_name
from milightsdriver.milight import Client, Controller, Off, Night


@click.group()
@click.option("--server", default="http://localhost:3000")
@click.pass_context
def main(ctx, server):
    client = Client(server)
    ctl = Controller(client)
    ctl.add_all()
    ctx.obj = ctl


@main.command()
@click.pass_context
def list(ctx):
    for name, zn in ctx.obj.zones.items():
        click.echo('{!s}: {!s} {}'.format(name, zn.mode.name, dict(zn.mode._asdict())))


@main.command()
@click.argument('zone')
@click.argument('mode')
@click.pass_context
def set(ctx, zone, mode):
    if mode == 'off':
        m = Off()
    elif mode == 'night':
        m = Night()
    else:
        m = color_by_name(mode)

    if zone == 'all':
        ctx.obj.set_all(m)
    else:
        ctx.obj.zone(zone).mode = m


if __name__ == '__main__':
    main(obj=None)