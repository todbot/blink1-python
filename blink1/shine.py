# -*- coding: utf-8 -*-
import click

from blink1.blink1 import Blink1ConnectionFailed, InvalidColor, blink1


@click.command()
@click.option('--color', default='white', help='What colour to set the Blink(1)')
@click.option('--fade', default=0.2, help='Fade time in seconds')
@click.option('--switch-off/--no-switch-off', default=False,
              help='Turn the blink(1) off again on exit')
@click.option('--serial', default=None, help='Serial number of the blink(1) to use')
def shine(color, fade, switch_off, serial):
    try:
        with blink1(switch_off=switch_off, serial_number=serial) as b1:
            b1.fade_to_color(fade * 1000.0, color)
    except Blink1ConnectionFailed as e:
        raise click.ClickException("no blink(1) found: %s" % e) from e
    except InvalidColor as e:
        raise click.ClickException("bad color: %s" % e) from e


if __name__ == '__main__':
    shine()
