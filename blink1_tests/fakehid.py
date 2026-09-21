"""
fakehid -- a stand-in for the `hid` module, so the suite can run with no
blink(1) attached.

The library's coupling to hidapi is small: two module functions and five
device methods. This fake implements exactly that surface and records
every feature report written, which is how tests assert on the wire
bytes.
"""

REPORT_ID = 0x01
REPORT_SIZE = 9

DEFAULT_SERIAL = "1A2B3C4D"
DEFAULT_FIRMWARE = "306"
PATTERN_LINES = 32


class FakeHidDevice:
    def __init__(self, module):
        self.module = module
        self.serial = None
        self.opened = False
        self.close_count = 0
        self.writes = []
        self.pattern = [(0, 0, 0, 0, 0)] * PATTERN_LINES
        self.ledn = 0
        self._response = [0] * REPORT_SIZE

    @property
    def closed(self):
        return self.close_count > 0

    def open(self, vendor_id, product_id, serial_number=None):
        if vendor_id != self.module.vendor_id or product_id != self.module.product_id:
            raise OSError("open failed")
        if not self.module.serials:
            raise OSError("open failed")
        if serial_number is not None and serial_number not in self.module.serials:
            raise OSError("open failed")
        self.serial = serial_number or self.module.serials[0]
        self.opened = True

    def send_feature_report(self, buf):
        if self.closed:
            raise OSError("device is closed")
        buf = list(buf)
        if len(buf) != REPORT_SIZE:
            raise ValueError("expected %d bytes, got %d" % (REPORT_SIZE, len(buf)))
        self.writes.append(buf)
        self._dispatch(buf)
        return REPORT_SIZE

    def get_feature_report(self, report_id, size):
        if self.closed:
            raise OSError("device is closed")
        return list(self._response)

    def get_serial_number_string(self):
        if self.closed:
            raise OSError("device is closed")
        return self.serial

    def close(self):
        self.close_count += 1
        self.opened = False

    def _dispatch(self, buf):
        cmd = buf[1]
        if cmd == ord("v"):
            n = int(self.module.firmware)
            self._response = [
                REPORT_ID, cmd, 0,
                ord(str(n // 100)), ord(str(n % 100)),
                0, 0, 0, 0,
            ]
        elif cmd == ord("l"):
            self.ledn = buf[2]
        elif cmd == ord("P"):
            pos = buf[7]
            if 0 <= pos < len(self.pattern):
                self.pattern[pos] = (buf[2], buf[3], buf[4], buf[5], buf[6])
        elif cmd == ord("R"):
            pos = buf[7]
            r, g, b, th, tl = (
                self.pattern[pos] if 0 <= pos < len(self.pattern) else (0, 0, 0, 0, 0)
            )
            self._response = [REPORT_ID, cmd, r, g, b, th, tl, pos, 0]


class FakeHidModule:
    """Drop-in replacement for the `hid` module as blink1.blink1 uses it."""

    def __init__(self, serials=None, firmware=DEFAULT_FIRMWARE,
                 vendor_id=0x27B8, product_id=0x01ED):
        self.serials = [DEFAULT_SERIAL] if serials is None else list(serials)
        self.firmware = firmware
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.devices = []

    def device(self, vendor_id=None, product_id=None, serial_number=None):
        """Real hidapi accepts and ignores these; the open() call does the work."""
        dev = FakeHidDevice(self)
        self.devices.append(dev)
        return dev

    def enumerate(self, vendor_id=None, product_id=None):
        return [
            {
                "serial_number": s,
                "vendor_id": self.vendor_id,
                "product_id": self.product_id,
                "product_string": "blink(1) mk3",
            }
            for s in self.serials
        ]

    @property
    def last_device(self):
        return self.devices[-1] if self.devices else None


class FakeHidMixin:
    """unittest mixin: swap in a fake `hid` for the duration of each test.

    Set `serials` / `firmware` on the subclass to vary the simulated
    device. Call `setUpFakeHid()` from `setUp`.
    """

    serials = None
    firmware = DEFAULT_FIRMWARE

    def setUpFakeHid(self):
        from unittest import mock

        import blink1.blink1 as blink1_mod

        self.fake_hid = FakeHidModule(serials=self.serials, firmware=self.firmware)
        patcher = mock.patch.object(blink1_mod, "hid", self.fake_hid)
        patcher.start()
        self.addCleanup(patcher.stop)
        return self.fake_hid
