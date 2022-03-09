from locations.hours import OpeningHours


def test_two_ranges():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Tu", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")

    o.add_range("Fr", "08:00", "17:00")
    o.add_range("Sa", "08:00", "17:00")

    assert o.as_opening_hours() == "Mo-We 07:00-17:00; Fr-Sa 08:00-17:00"


def test_mixed_ranges():
    o = OpeningHours()
    o.add_range("Mo", "08:00", "17:00")
    o.add_range("Tu", "08:00", "17:00")
    o.add_range("We", "09:00", "18:00")
    o.add_range("Th", "09:00", "18:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Su", "09:00", "17:00")

    assert (
        o.as_opening_hours()
        == "Mo-Tu 08:00-17:00; We-Th 09:00-18:00; Fr 07:00-17:00; Su 09:00-17:00"
    )


def test_closed_sunday():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Tu", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")
    o.add_range("Th", "07:00", "17:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Sa", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo-Sa 07:00-17:00"


def test_closed_tuesday():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")
    o.add_range("Th", "07:00", "17:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Sa", "07:00", "17:00")
    o.add_range("Su", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo 07:00-17:00; We-Su 07:00-17:00"


def test_twentyfour_seven():
    o = OpeningHours()
    o.add_range("Mo", "0:00", "23:59")
    o.add_range("Tu", "0:00", "23:59")
    o.add_range("We", "0:00", "23:59")
    o.add_range("Th", "0:00", "23:59")
    o.add_range("Fr", "0:00", "23:59")
    o.add_range("Sa", "0:00", "23:59")
    o.add_range("Su", "0:00", "23:59")

    assert o.as_opening_hours() == "24/7"


def test_no_opening_hours():
    o = OpeningHours()
    assert o.as_opening_hours() == ""
