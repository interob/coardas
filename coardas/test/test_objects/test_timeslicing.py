from datetime import datetime

from copernicus_ndvi.objects.timeslicing import Dekad


def test_dekadal_timeslicing():
    d = Dekad(2023, 2)
    assert d.year == 2023
    assert d.month == 1
    assert d.day == 11

    d += 2
    assert d.year == 2023
    assert d.month == 2
    assert d.day == 1

    d = Dekad(datetime(2022, 11, 2))
    assert d.year == 2022
    assert d.month == 11
    assert d.day == 1
