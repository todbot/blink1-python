import unittest

import pytest

from blink1.blink1 import (
    READ_SIZE,
    REPORT_ID,
    REPORT_SIZE,
    Blink1,
    Blink1ConnectionFailed,
    InvalidColor,
)

from .fakehid import DEFAULT_SERIAL, FakeHidMixin


class LightControlChecks:
    """Assertions that hold whether the device is real or faked.

    `self.b1` is supplied by the concrete subclass.
    """

    def testOn(self):
        self.b1.fade_to_color(1000, 'white')

    def testInvalidColor(self):
        with self.assertRaises(InvalidColor):
            self.b1.fade_to_color(1000, 'moomintrol')

    def testAlsoWhite(self):
        self.b1.fade_to_color(1000, (255, 255, 255))

    def testAWhiteShadeOfPale(self):
        self.b1.fade_to_color(1000, '#ffffff')

    def testAGreyerShadeOfPale(self):
        self.b1.fade_to_color(1000, '#eeeeee')

    def testAnImplausibleShadeOfWhite(self):
        with self.assertRaises(InvalidColor):
            self.b1.fade_to_color(1000, '#xxxxxx')

    def testOff(self):
        self.b1.off()

    def test_get_firmware_version(self):
        version = self.b1.get_version()
        self.assertTrue(version.isdigit(), version)
        self.assertGreater(int(version), 0)

    def test_read_report_is_shorter_than_a_write(self):
        """Reads come back with 8 bytes though writes take 9.

        Runs against both the fake and real hardware, so the fake cannot
        drift back to mirroring the write size.
        """
        self.b1.get_version()
        self.assertEqual(len(self.b1.read()), READ_SIZE)

    def test_get_serial_number(self):
        self.assertTrue(self.b1.get_serial_number())


class TestSimpleLightControlFake(FakeHidMixin, LightControlChecks, unittest.TestCase):
    def setUp(self):
        self.setUpFakeHid()
        self.b1 = Blink1(pattern_lines=32)
        self.addCleanup(self.b1.close)

    def test_serial_matches_enumeration(self):
        self.assertEqual(self.b1.get_serial_number(), DEFAULT_SERIAL)
        self.assertEqual(Blink1.list(), [DEFAULT_SERIAL])

    def test_read_requests_the_full_report_size(self):
        """Windows fails a read that asks for less than the report length.

        The size asked for and the size that comes back are different
        numbers; requesting READ_SIZE here broke Windows once already.
        """
        self.b1.get_version()
        self.assertEqual(self.fake_hid.last_device.reads[-1],
                         (REPORT_ID, REPORT_SIZE))

    def test_read_tolerates_a_longer_response(self):
        """Some platforms hand back more than READ_SIZE; that is not an error."""
        self.fake_hid.last_device.extra_read_bytes = 1
        self.assertEqual(len(self.b1.read()), READ_SIZE + 1)
        self.assertTrue(self.b1.get_version().isdigit())

    def test_version_from_firmware(self):
        self.assertEqual(self.b1.get_version(), '306')


@pytest.mark.hardware
class TestSimpleLightControl(LightControlChecks, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b1 = Blink1()

    @classmethod
    def tearDownClass(cls):
        cls.b1.off()
        cls.b1.close()
        del cls.b1


class TestFailedConnection(FakeHidMixin, unittest.TestCase):
    serials = []

    def setUp(self):
        self.setUpFakeHid()

    def testCannotFind(self):
        with self.assertRaises(Blink1ConnectionFailed):
            Blink1()

    def testCannotFindBySerial(self):
        self.fake_hid.serials = ['AAAA1111']
        with self.assertRaises(Blink1ConnectionFailed):
            Blink1(serial_number='NOSUCH')

    def testListIsEmpty(self):
        self.assertEqual(Blink1.list(), [])


if __name__ == '__main__':
    unittest.main()
