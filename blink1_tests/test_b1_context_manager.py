import time
import unittest

import pytest

from blink1.blink1 import Blink1ConnectionFailed, blink1
from blink1.kelvin import COLOR_TEMPERATURES

from .fakehid import FakeHidMixin


class ContextManagerChecks:
    """Assertions that hold whether the device is real or faked."""

    def test_cm(self):
        with blink1(pattern_lines=32) as b1:
            b1.fade_to_color(0, "teal")

    def test_cm_with_gamma(self):
        with blink1(pattern_lines=32, gamma=(.5, .5, .5)) as b1:
            b1.fade_to_color(0, "teal")

    def test_cm_with_white_point_tuple(self):
        with blink1(pattern_lines=32, white_point=(255, 255, 255)) as b1:
            b1.fade_to_color(0, "white")
            time.sleep(0.1)

    def test_cm_with_white_point_kelvin(self):
        with blink1(pattern_lines=32, white_point=COLOR_TEMPERATURES['candle']) as b1:
            b1.fade_to_color(0, "white")
            time.sleep(0.1)

    def test_cm_with_white_point_name(self):
        with blink1(pattern_lines=32, white_point='blue-sky') as b1:
            b1.fade_to_color(0, "white")
            time.sleep(0.1)


class TestBlink1ContextManagerFake(FakeHidMixin, ContextManagerChecks, unittest.TestCase):
    def setUp(self):
        self.setUpFakeHid()

    def test_cm_closes_device(self):
        with blink1(pattern_lines=32) as b1:
            b1.fade_to_color(0, "teal")
        self.assertTrue(self.fake_hid.last_device.closed)

    def test_cm_closed(self):
        with blink1(pattern_lines=32) as b1:
            b1.close()
            with self.assertRaises(Blink1ConnectionFailed):
                b1.fade_to_color(0, "teal")

    def test_close_is_idempotent(self):
        with blink1(pattern_lines=32, switch_off=False) as b1:
            b1.close()
            b1.close()
        self.assertEqual(self.fake_hid.last_device.close_count, 1)

    def test_exception_in_body_still_closes(self):
        with self.assertRaises(ZeroDivisionError):
            with blink1(pattern_lines=32) as b1:
                b1.fade_to_color(0, "teal")
                raise ZeroDivisionError("boom")
        self.assertTrue(self.fake_hid.last_device.closed)

    def test_blink1_class_is_a_context_manager(self):
        from blink1.blink1 import Blink1
        with Blink1(pattern_lines=32) as b1:
            b1.fade_to_color(0, "teal")
        self.assertTrue(self.fake_hid.last_device.closed)


@pytest.mark.hardware
class TestBlink1ContextManager(ContextManagerChecks, unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
