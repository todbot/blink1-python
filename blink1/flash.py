# -*- coding: utf-8 -*-
import time

import click

from blink1.blink1 import Blink1, Blink1ConnectionFailed, InvalidColor


@click.command()
@click.option('--on', default='white', help='Color to flash on')
@click.option('--off', default='black', help='Color to flash off')
@click.option('--duration', default=1.0, help='Length of each flash cycle in seconds')
@click.option('--repeat', default=2, help='Number of times to flash')
@click.option('--fade', default=0.2, help='Fade time in seconds')
@click.option('--serial', default=None, help='Serial number of the blink(1) to use')
def flash(on, off, duration, repeat, fade, serial):
    try:
        b1 = Blink1(serial_number=serial)
    except Blink1ConnectionFailed as e:
        raise click.ClickException("no blink(1) found: %s" % e) from e

    try:
        for _ in range(repeat):
            b1.fade_to_color(fade * 1000, on)
            time.sleep(duration / 2.0)
            b1.fade_to_color(fade * 1000, off)
            time.sleep(duration / 2.0)

        b1.fade_to_color(fade * 1000, 'black')
    except InvalidColor as e:
        raise click.ClickException("bad color: %s" % e) from e
    finally:
        b1.close()


if __name__ == '__main__':
    flash()
