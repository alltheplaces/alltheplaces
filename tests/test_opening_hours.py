import json
import time

from locations.hours import (
    DAYS,
    DAYS_BG,
    DAYS_DE,
    DAYS_ES,
    DAYS_RU,
    DELIMITERS_ES,
    DELIMITERS_RU,
    NAMED_DAY_RANGES_RU,
    NAMED_TIMES_RU,
    OpeningHours,
    day_range,
    sanitise_day,
)


def test_day_range():
    for day in DAYS:
        assert day_range(day, day) == [day]
    for day, next_day in zip(DAYS, DAYS[1:] + DAYS[:1]):
        assert sorted(day_range(next_day, day), key=DAYS.index) == DAYS


def test_duplicates():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Mo", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo 07:00-17:00"


def test_times():
    o = OpeningHours()
    o.add_range("Mo", time.strptime("07:00", "%H:%M"), time.strptime("17:00", "%H:%M"))
    o.add_range("Tu", "09:00", "19:00")

    assert o.as_opening_hours() == "Mo 07:00-17:00; Tu 09:00-19:00"


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

    assert o.as_opening_hours() == "Mo-Tu 08:00-17:00; We-Th 09:00-18:00; Fr 07:00-17:00; Su 09:00-17:00"


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


def test_multiple_times():
    o = OpeningHours()
    o.add_range("Mo", "08:00", "12:00")
    o.add_range("Mo", "13:00", "17:30")
    assert o.as_opening_hours() == "Mo 08:00-12:00,13:00-17:30"

    o2 = OpeningHours()
    o2.add_range("Tu", "09:00", "12:00")
    o2.add_range("Tu", "15:00", "17:00")
    assert o2.as_opening_hours() == "Tu 09:00-12:00,15:00-17:00"

    o3 = OpeningHours()
    o3.add_range("Tu", "15:00", "17:00")
    o3.add_range("Tu", "09:00", "12:00")
    assert o3.as_opening_hours() == "Tu 09:00-12:00,15:00-17:00"


def test_sanitise_days():
    assert sanitise_day("Mo") == "Mo"
    assert sanitise_day("Mon") == "Mo"
    assert sanitise_day("MONDAY") == "Mo"
    assert sanitise_day("schema.org/monday") == "Mo"
    assert sanitise_day("https://schema.org/monday") == "Mo"
    assert sanitise_day("http://schema.org/monday") == "Mo"
    assert sanitise_day("http://purl.org/goodrelations/v1#Monday") == "Mo"
    assert sanitise_day("   Monday ") == "Mo"
    assert sanitise_day("not_a_day") is None
    assert sanitise_day("пон", DAYS_BG) == "Mo"
    assert sanitise_day("Съб. ", DAYS_BG) == "Sa"
    assert sanitise_day("Съб. ", DAYS_DE) is None
    assert sanitise_day("Mo", DAYS_DE) == "Mo"
    assert sanitise_day("Do", DAYS_DE) == "Th"


def test_ld_parse():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Store",
                "name": "Middle of Nowhere Foods",
                "openingHoursSpecification":
                [
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": [
                            "http://schema.org/Monday",
                            "https://schema.org/Tuesday",
                            "Wednesday",
                            "http://schema.org/Thursday",
                            "http://schema.org/Friday"
                        ],
                        "opens": "09:00",
                        "closes": "11:00"
                    },
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": "http://schema.org/Saturday",
                        "opens": "12:00",
                        "closes": "14:00"
                    }
                ]
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Fr 09:00-11:00; Sa 12:00-14:00"


def test_ld_parse_opening_hours():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "name": "Philippa's Pharmacy",
                "description": "A superb collection of fine pharmaceuticals for your beauty and healthcare convenience, a department of Delia's Drugstore.",
                "openingHours": "Mo,Tu,We,Th 09:00-12:00",
                "telephone": "+18005551234"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Th 09:00-12:00"

    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "name": "Philippa's Pharmacy",
                "description": "A superb collection of fine pharmaceuticals for your beauty and healthcare convenience, a department of Delia's Drugstore.",
                "openingHours": "Mo-Th 09:00-12:00",
                "telephone": "+18005551234"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Th 09:00-12:00"

    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "name": "Philippa's Pharmacy",
                "description": "A superb collection of fine pharmaceuticals for your beauty and healthcare convenience, a department of Delia's Drugstore.",
                "openingHours": "Mo-Tu 09:00-12:00 We,Th 09:00-12:00",
                "telephone": "+18005551234"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Th 09:00-12:00"


def test_ld_parse_opening_hours_days_3_chars():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "name": "Philippa's Pharmacy",
                "description": "A superb collection of fine pharmaceuticals for your beauty and healthcare convenience, a department of Delia's Drugstore.",
                "openingHours": "Mon-Thu 09:00-12:00",
                "telephone": "+18005551234"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Th 09:00-12:00"

    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "name": "Philippa's Pharmacy",
                "description": "A superb collection of fine pharmaceuticals for your beauty and healthcare convenience, a department of Delia's Drugstore.",
                "openingHours": "Mon-Tue 09:00-12:00 Wed,Thu 09:00-12:00",
                "telephone": "+18005551234"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Th 09:00-12:00"

    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Pharmacy",
                "openingHours": "Mon-Sat 10:00 - 19:00 Sun 12:00-17:00"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Sa 10:00-19:00; Su 12:00-17:00"


def test_ld_parse_opening_hours_array():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": ["TouristAttraction", "AmusementPark"],
                "name": "Disneyland Paris",
                "description": "It's an amusement park in Marne-la-Vallée, near Paris, in France and is the most visited theme park in all of France and Europe.",
                "openingHours":["Mo-Fr 10:00-19:00", "Sa 10:00-22:00", "Su 10:00-21:00"],
                "isAccessibleForFree": false,
                "currenciesAccepted": "EUR",
                "paymentAccepted":"Cash, Credit Card",
                "url":"http://www.disneylandparis.it/"
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Fr 10:00-19:00; Sa 10:00-22:00; Su 10:00-21:00"


def test_ld_parse_opening_hours_day_range():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "openingHours": ["Th-Tu 09:00-17:00"]
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Tu 09:00-17:00; Th-Su 09:00-17:00"


def test_ld_parse_opening_hours_array_with_commas():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "openingHours": ["Mo-Su 00:00-01:00, 04:00-00:00"]
            }
            """
        )
    )
    assert o.as_opening_hours() == "Mo-Su 00:00-01:00,04:00-24:00"


def test_ld_parse_time_format():
    o = OpeningHours()
    o.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Store",
                "name": "Middle of Nowhere Foods",
                "openingHoursSpecification":
                [
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": "http://schema.org/Saturday",
                        "opens": "12:00:00",
                        "closes": "14:00:00"
                    }
                ]
            }
            """
        ),
        "%H:%M:%S",
    )
    assert o.as_opening_hours() == "Sa 12:00-14:00"


def test_add_ranges_from_string():
    o = OpeningHours()
    o.add_ranges_from_string("Monday-Wednesday: 5pm - 7pm")
    o.add_ranges_from_string("Monday-Wednesday 08:00-14:00")
    o.add_ranges_from_string("Monday to Tuesday: 15:00:01 to 16:35")
    o.add_ranges_from_string("Thurs 2PM-6:30P.M.")
    o.add_ranges_from_string(" Fri    9 a.m.  -  11am ")
    o.add_ranges_from_string("Weekends: 8:00 AM to 6:00 PM")
    assert (
        o.as_opening_hours()
        == "Mo-Tu 08:00-14:00,15:00-16:35,17:00-19:00; We 08:00-14:00,17:00-19:00; Th 14:00-18:30; Fr 09:00-11:00; Sa-Su 08:00-18:00"
    )

    o = OpeningHours()
    o.add_ranges_from_string("Monday to Thursday 7am to 7pm, Friday 12am to 11:59pm, Weekends CLOSED")
    assert o.as_opening_hours() == "Mo-Th 07:00-19:00; Fr 00:00-24:00"

    o = OpeningHours()
    o.add_ranges_from_string("Sunday to Thursday 0800-1400, Wed-Sat 1300-1800")
    assert o.as_opening_hours() == "Mo-Tu 08:00-14:00; We-Th 08:00-14:00,13:00-18:00; Fr-Sa 13:00-18:00; Su 08:00-14:00"

    o = OpeningHours()
    o.add_ranges_from_string("Monday - Sunday: 00:00 - 23:59")
    assert o.as_opening_hours() == "24/7"

    o = OpeningHours()
    o.add_ranges_from_string("Monday: 08:00 - Midday, 14:00 - Midnight   tue-sat: Midnight-0800")
    assert o.as_opening_hours() == "Mo 08:00-12:00,14:00-24:00; Tu-Sa 00:00-08:00"

    o = OpeningHours()
    o.add_ranges_from_string("Wed 2am-3am, 11am-1pm, 6pm-7pm, Thu midday-3:30pm 4:30pm-5:15pm")
    assert o.as_opening_hours() == "We 02:00-03:00,11:00-13:00,18:00-19:00; Th 12:00-15:30,16:30-17:15"

    o = OpeningHours()
    o.add_ranges_from_string(
        "Lunes a Domingo: 11:00 a 20:30 / Viernes y Sábado: 11:00 a 21:00",
        days=DAYS_ES,
        named_day_ranges={},
        delimiters=DELIMITERS_ES,
    )
    o.add_ranges_from_string(
        "Lunes a Sábado de 09:00 a 10:15 / Domingo de 09:00:00 a 10:00:00",
        days=DAYS_ES,
        named_day_ranges={},
        delimiters=DELIMITERS_ES,
    )
    assert (
        o.as_opening_hours()
        == "Mo-Th 09:00-10:15,11:00-20:30; Fr-Sa 09:00-10:15,11:00-20:30,11:00-21:00; Su 09:00-10:00,11:00-20:30"
    )

    o = OpeningHours()
    o.add_ranges_from_string(
        "{Sun|056:00AM-08:00PM}{Mon|05:00AM-09:00PM}{Tue|05:00AM-09:00PM}{Wed|05:00AM-09:00PM}{Thu|05:00AM-09:00PM}{Fri|05:00AM-09:00PM}{Sat|c}"
    )
    assert o.as_opening_hours() == "Mo-Fr 05:00-21:00"

    o = OpeningHours()
    o.add_ranges_from_string("Mo-Tu 06-12,We 14-18:30,Th 09-17,Fr 04-24,Sa-Su 00:00-11:59")
    assert (
        o.as_opening_hours() == "Mo-Tu 06:00-12:00; We 14:00-18:30; Th 09:00-17:00; Fr 04:00-24:00; Sa-Su 00:00-11:59"
    )

    o = OpeningHours()
    o.add_ranges_from_string(
        "[по будням: 10:00 - 21:00], [в субботу: 10:00 - 20:00], [в воскресенье: 10:00 - 21:00]",
        DAYS_RU,
        NAMED_DAY_RANGES_RU,
        NAMED_TIMES_RU,
        DELIMITERS_RU,
    )
    assert o.as_opening_hours() == "Mo-Fr 10:00-21:00; Sa 10:00-20:00; Su 10:00-21:00"
