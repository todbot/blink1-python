"""The flat namespace, without breaking any existing import spelling."""

import subprocess
import sys

import blink1
import blink1.blink1


def _run(code):
    """Import from a directory that is not the repo root."""
    return subprocess.run(
        [sys.executable, "-c", code], cwd="/", capture_output=True, text=True
    )


def test_flat_import():
    from blink1 import Blink1, Blink1ConnectionFailed, InvalidColor
    assert Blink1 is blink1.blink1.Blink1
    assert issubclass(Blink1ConnectionFailed, RuntimeError)
    assert issubclass(InvalidColor, ValueError)


def test_legacy_import_still_works():
    from blink1.blink1 import Blink1, ColorCorrect, blink1 as blink1_cm
    assert Blink1 is blink1.blink1.Blink1
    assert callable(blink1_cm)
    assert ColorCorrect is blink1.blink1.ColorCorrect


def test_package_attribute_is_still_the_module():
    """Re-exporting the context manager as `blink1` would shadow this."""
    import types
    assert isinstance(blink1.blink1, types.ModuleType)
    assert blink1.blink1.Blink1 is not None


def test_module_alias_resolves_to_the_module():
    import blink1.blink1 as m
    assert m.Blink1 is blink1.blink1.Blink1


def test_context_manager_exported_as_blink1_ctx():
    assert blink1.blink1_ctx is blink1.blink1.blink1


def test_version_is_a_string():
    assert isinstance(blink1.__version__, str)
    assert blink1.__version__


def test_all_names_resolve():
    for name in blink1.__all__:
        assert hasattr(blink1, name), name


def test_import_spellings_outside_the_repo():
    """Guards against the stale egg-info in the repo root masking a problem."""
    for code in (
        "from blink1 import Blink1, blink1_ctx, __version__",
        "from blink1.blink1 import Blink1, blink1, ColorCorrect",
        "import blink1.blink1; assert blink1.blink1.Blink1",
        "import blink1.blink1 as m; assert m.Blink1",
    ):
        result = _run(code)
        assert result.returncode == 0, "%s -> %s" % (code, result.stderr)
