# -*- coding: utf-8 -*-
import click
from blink1.blink1 import blink1


@click.command()
@click.option('--color', default='white', help='What colour to set the Blink(1)')
@click.option('--fade', default=0.2, help='Fade time in seconds')
def shine(color, fade):
    with blink1(switch_off=False) as b1:
        b1.fade_to_color(fade * 1000.0, color)


if __name__ == '__main__':
    shine()
