# Changelog

## 1.1.0 (unreleased)

### Added

Three gaps against the C library, `blink1-lib`, all additive:

- `read_rgb(ledn=0)` returns the current color of an LED as
  `(r, g, b, fade_millis)`. Takes `uncorrect=True`, like
  `read_pattern_line`, to undo the gamma correction applied on the way
  out. Note `fade_millis` is part of the protocol but an mk3 on firmware
  302 always answers 0 for it.
- `read_play_state()` returns a `PlayState` named tuple of
  `(playing, start_pos, end_pos, repeats, pos)`, so you can tell whether
  a pattern is running and how far through it is. `repeats` is the number
  of plays left, 0 meaning forever; it is not called `count` because that
  would shadow `tuple.count`.
- `get_startup_params()` and `set_startup_params()` read and write what
  the blink(1) does when powered with no computer attached, with
  `BOOT_NORMAL`, `BOOT_PLAY` and `BOOT_OFF` exported for the mode. The
  setting is non-volatile. Needs firmware 206+ or an mk3; older devices
  do not implement the commands and fail silently.
- `color_to_rgb()` now accepts the remaining forms `blink1-tool` takes:
  a bare hexcode `FF00FF`, and decimal or hex triples `255,0,255` and
  `0xff,0x00,0xff`. Named colors, `#ff00ff`, tuples and lists work as
  before, and a name is still tried ahead of bare hex so no existing
  color name changes meaning.

`PlayState`, `StartupParams` and the three `BOOT_*` constants are
exported from the package.

## 1.0.1 - 21 Sep 2026

### Fixed

- Reading from the device failed on Windows with `OSError: read error`.
  A feature report read has to request the full 9-byte report size;
  Windows rejects a shorter buffer, while macOS and Linux return 8 bytes
  whatever is asked for. 1.0.0 requested 8, the number of bytes that come
  back, which is a different thing from the number that must be asked for.

  On Windows under 1.0.0 this meant `get_version()`, `read_pattern_line()`
  and `read_pattern()` all raised, and because pattern-size detection
  swallows errors and falls back to the mk3 size, `Blink1()` still opened
  but always reported `pattern_lines` as 32, which is wrong on an mk2.

## 1.0.0 - 21 Sep 2026

### Changed

Five behavior changes a 0.4.0 user may notice:

- `COLOR_TEMPERATURES['fluorescent']` is 3750, not 37500. The old value
  was a typo, and a silent one: 37500K is inside the conversion's valid
  range, so it returned a plausible deep blue instead of failing. Code
  using that white point will now see a different color.
- Color tuples are validated. A tuple or list that is not three channels
  of 0-255 raises `InvalidColor` instead of being passed to the device.
  This is what the README has always promised.
- `close()` is idempotent, and calling any method on a closed device
  raises `Blink1ConnectionFailed` rather than `AttributeError`.
- `ledn` outside 0-2, and a pattern `pos` outside the device's pattern
  memory, raise `ValueError` instead of writing a bad byte.
- `kelvin_to_rgb` clamps its input to 1000-40000K. `kelvin_to_rgb(0)`
  previously raised `ValueError: math domain error`.

Everything else is additive; existing names and call signatures still
work, `onDevice` and `Blink1.notfound()` included.

### Added

- Flat namespace: `from blink1 import Blink1`. The context manager is
  re-exported as `blink1_ctx`, not `blink1`, so `import blink1.blink1`
  keeps resolving to the module.
- `Blink1` is a context manager in its own right.
- `Blink1(pattern_lines=...)`, and detection of pattern memory size from
  the firmware version (16 lines on mk2, 32 on mk3) when it is not given.
- `play_pattern(..., on_device=...)` as a snake_case alias for `onDevice`.
- `read_pattern_line(..., uncorrect=True)` to undo the gamma correction
  `write_pattern_line` applies, so read-modify-write does not compound it.
- `blink1()` takes `serial_number` and `pattern_lines`.
- `UnknownWhitePoint`, raised for an unknown white point name. It
  subclasses both `InvalidColor` and `KeyError`, so code catching the
  old bare `KeyError` still works.
- `blink1-shine --switch-off`, and `--serial` on both CLI scripts. Both
  now report a missing device or bad color as a one-line error.
- `blink1-shine --list` prints the serial numbers of connected blink(1)s,
  and `--version` prints the library version plus the device firmware
  version when one is attached. Neither needs a device to run.
- Type hints on the public API, with `py.typed`.
- A test suite that runs with no hardware attached, via a fake HID layer.
  Tests needing a real device are marked and skipped unless
  `--run-hardware` is passed.
- GitHub Actions CI across Python 3.9-3.13 on Linux, plus macOS and
  Windows.

### Fixed

- `parse_pattern` no longer crashes on empty fields, so pattern strings
  like `'2,#ff99cc,,0.3'` parse. One such string ships in
  `blink1_demo/demo_pattern3.py`.
- The `blink1()` context manager cleans up in a `finally`. An exception
  inside the `with` block previously left the light on and leaked the
  HID handle.
- `flash` closes its device; it never did.
- `blink1-flash --duration 1.5` is accepted. The default of `1` made
  click infer an integer.
- `demo_serial_version.py` called `sys.exit()` without importing `sys`,
  so its "no device" path raised `NameError`.

### Packaging

- `requires-python = ">=3.9"`, a `dev` extra, lower bounds on `click`
  and `webcolors`, and current classifiers and URLs.
- setuptools floor raised to 77, which is what the PEP 639
  `license = "MIT"` form needs.
