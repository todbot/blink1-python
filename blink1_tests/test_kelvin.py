import time
import unittest

import pytest

from blink1.blink1 import blink1
from blink1.kelvin import COLOR_TEMPERATURES, KELVIN_MIN, KELVIN_MAX, kelvin_to_rgb


class TestKelvin(unittest.TestCase):

    def test_red_6000(self):
        r, g, b = kelvin_to_rgb(6000)
        self.assertEqual(r, 255)

    def test_blue_6700(self):
        r, g, b = kelvin_to_rgb(6700)
        self.assertEqual(b, 255)

    def test_range(self):
        """Verify that it is possible to produce the entire color range"""
        for k in range(10, 12000, 400):
            r, g, b = kelvin_to_rgb(k)
            self.assertIsInstance(r, int)
            self.assertIsInstance(g, int)
            self.assertIsInstance(b, int)
            self.assertTrue(0 <= r <= 255)
            self.assertTrue(0 <= g <= 255)
            self.assertTrue(0 <= b <= 255)


@pytest.mark.hardware
class TestKelvinOnDevice(unittest.TestCase):

    def test_range_on_device(self):
        for k in range(10, 12000, 400):
            r, g, b = kelvin_to_rgb(k)
            with blink1(white_point=(r, g, b)) as b1:
                b1.fade_to_color(0, 'white')
                time.sleep(0.05)


if __name__ == '__main__':
    unittest.main()


class TestKelvinRange(unittest.TestCase):
    """The domain guard: math.log used to blow up on low inputs."""

    def test_zero_does_not_raise(self):
        self.assertEqual(len(kelvin_to_rgb(0)), 3)

    def test_negative_does_not_raise(self):
        r, g, b = kelvin_to_rgb(-500)
        self.assertTrue(all(0 <= c <= 255 for c in (r, g, b)))

    def test_absurdly_high_does_not_raise(self):
        r, g, b = kelvin_to_rgb(1_000_000)
        self.assertTrue(all(0 <= c <= 255 for c in (r, g, b)))

    def test_clamps_to_the_documented_range(self):
        self.assertEqual(kelvin_to_rgb(0), kelvin_to_rgb(KELVIN_MIN))
        self.assertEqual(kelvin_to_rgb(10 ** 6), kelvin_to_rgb(KELVIN_MAX))

    def test_fluorescent_sits_between_its_neighbours(self):
        """37500 was a typo for 3750, silent because it stayed in range."""
        self.assertEqual(COLOR_TEMPERATURES['fluorescent'], 3750)
        self.assertLess(
            COLOR_TEMPERATURES['warm-fluorescent'],
            COLOR_TEMPERATURES['fluorescent'],
        )
        self.assertLess(
            COLOR_TEMPERATURES['fluorescent'],
            COLOR_TEMPERATURES['cool-fluorescent'],
        )

    def test_every_named_temperature_converts(self):
        for name, k in COLOR_TEMPERATURES.items():
            r, g, b = kelvin_to_rgb(k)
            self.assertTrue(all(0 <= c <= 255 for c in (r, g, b)), name)
