# -*- coding: utf-8 -*-
import click

from blink1 import __version__
from blink1.blink1 import Blink1, Blink1ConnectionFailed, InvalidColor, blink1


@click.command()
@click.option('--color', default='white', help='What colour to set the Blink(1)')
@click.option('--fade', default=0.2, help='Fade time in seconds')
@click.option('--switch-off/--no-switch-off', default=False,
              help='Turn the blink(1) off again on exit')
@click.option('--serial', default=None, help='Serial number of the blink(1) to use')
@click.option('--list', 'list_devices', is_flag=True,
              help='List the serial numbers of connected blink(1)s and exit')
@click.option('--version', 'show_version', is_flag=True,
              help='Show library and firmware versions and exit')
def shine(color, fade, switch_off, serial, list_devices, show_version):
    if list_devices:
        serials = Blink1.list()
        for s in serials:
            click.echo(s)
        if not serials:
            click.echo('no blink(1) devices found')
        return

    if show_version:
        click.echo('blink1 python library %s' % __version__)
        try:
            # switch_off=False so asking the version never alters the light
            with blink1(switch_off=False, serial_number=serial) as b1:
                click.echo('blink(1) firmware %s (serial %s)'
                           % (b1.get_version(), b1.get_serial_number()))
        except Blink1ConnectionFailed:
            click.echo('no blink(1) connected')
        return

    try:
        with blink1(switch_off=switch_off, serial_number=serial) as b1:
            b1.fade_to_color(fade * 1000.0, color)
    except Blink1ConnectionFailed as e:
        raise click.ClickException("no blink(1) found: %s" % e) from e
    except InvalidColor as e:
        raise click.ClickException("bad color: %s" % e) from e


if __name__ == '__main__':
    shine()
