import importlib.util
from pathlib import Path

# Load spider module that starts with a number
spider_path = Path(__file__).parent.parent / "locations" / "spiders" / "99_speedmart_my.py"
spec = importlib.util.spec_from_file_location("speedmart_my", spider_path)
speedmart_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speedmart_module)

dms_to_decimal = speedmart_module.dms_to_decimal


def test_dms_to_decimal_simple_degrees():
    """Test simple degree conversion without minutes/seconds."""
    assert dms_to_decimal("45°N") == 45.0
    assert dms_to_decimal("45°S") == -45.0
    assert dms_to_decimal("120°E") == 120.0
    assert dms_to_decimal("120°W") == -120.0


def test_dms_to_decimal_degrees_minutes():
    """Test degree and minute conversion."""
    assert dms_to_decimal("51°30'N") == 51.5
    assert dms_to_decimal("51°30'S") == -51.5


def test_dms_to_decimal_full_dms():
    """Test full DMS (degrees, minutes, seconds) conversion."""
    # 3°16'51.1"N = 3 + 16/60 + 51.1/3600 = 3.280858...
    result = dms_to_decimal("3°16'51.1\"N")
    assert abs(result - 3.280858) < 0.0001

    # Same but with South (negative)
    result = dms_to_decimal("3°16'51.1\"S")
    assert abs(result - (-3.280858)) < 0.0001

    # 101°18'54.7"E
    result = dms_to_decimal("101°18'54.7\"E")
    assert abs(result - 101.315194) < 0.0001

    # Same but with West (negative)
    result = dms_to_decimal("101°18'54.7\"W")
    assert abs(result - (-101.315194)) < 0.0001


def test_dms_to_decimal_with_whitespace():
    """Test DMS parsing with variable whitespace."""
    result1 = dms_to_decimal("3°16'51.1\"N")
    result2 = dms_to_decimal("3° 16' 51.1\" N")
    assert abs(result1 - result2) < 0.0001
