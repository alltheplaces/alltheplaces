import re
import time
from collections import defaultdict

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
DAYS_FULL = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

DAYS_EN = {
    "Monday": "Mo",
    "Mon": "Mo",
    "Mo": "Mo",
    "Tuesday": "Tu",
    "Tues": "Tu",
    "Tue": "Tu",
    "Tu": "Tu",
    "Wednesday": "We",
    "Weds": "We",
    "Wed": "We",
    "We": "We",
    "Thursday": "Th",
    "Thu": "Th",
    "Thur": "Th",
    "Thrs": "Th",
    "Thurs": "Th",
    "Th": "Th",
    "Friday": "Fr",
    "Fri": "Fr",
    "Fr": "Fr",
    "Saturday": "Sa",
    "Sat": "Sa",
    "Sa": "Sa",
    "Sunday": "Su",
    "Sun": "Su",
    "Su": "Su",
}
DAYS_DE = {
    "Montag": "Mo",
    "Mo": "Mo",
    "Dienstag": "Tu",
    "Di": "Tu",
    "Mittwoch": "We",
    "Mi": "We",
    "Donnerstag": "Th",
    "Do": "Th",
    "Freitag": "Fr",
    "Fr": "Fr",
    "Samstag": "Sa",
    "Sa": "Sa",
    "Sonntag": "Su",
    "So": "Su",
}
DAYS_BG = {
    "Понеделник": "Mo",
    "Пн": "Mo",
    "Пон": "Mo",
    "По": "Mo",
    "Вторник": "Tu",
    "Вт": "Tu",
    "Сряда": "We",
    "Ср": "We",
    "Четвъртък": "Th",
    "Че": "Th",
    "Чт": "Th",
    "Петък": "Fr",
    "Пет": "Fr",
    "Пе": "Fr",
    "Пт": "Fr",
    "Събота": "Sa",
    "Съб": "Sa",
    "Съ": "Sa",
    "Сб": "Sa",
    "Неделя": "Su",
    "нед": "Su",
    "Не": "Su",
    "Нд": "Su",
}
DAYS_CH = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}
DAYS_CZ = {
    "Pondělí": "Mo",
    "Po": "Mo",
    "Úterý": "Tu",
    "Út": "Tu",
    "Středa": "We",
    "St": "We",
    "Čtvrtek": "Th",
    "Čt": "Th",
    "Pátek": "Fr",
    "Pá": "Fr",
    "Sobota": "Sa",
    "So": "Sa",
    "Neděle": "Su",
    "Ne": "Su",
}
DAYS_GR = {
    "Δε": "Mo",
    "Τρ": "Tu",
    "Τε": "We",
    "Πέ": "Th",
    "Πα": "Fr",
    "Σά": "Sa",
    "Κυ": "Su",
}
DAYS_HU = {
    "Hétfő": "Mo",
    "Hé": "Mo",
    "H": "Mo",
    "Kedd": "Tu",
    "Ke": "Tu",
    "K": "Tu",
    "Szerda": "We",
    "Sze": "We",
    # "Sz": "We",
    "Csütörtök": "Th",
    "Csü": "Th",
    "Cs": "Th",
    "Péntek": "Fr",
    "Pé": "Fr",
    "P": "Fr",
    "Szombat": "Sa",
    "Szo": "Sa",
    # "Sz": "Sa",
    "Va": "Sa",
    "V": "Su",
    "Vasárnap": "Su",
    "Vas": "Su",
}

DAYS_SE = {
    "Måndag": "Mo",
    "Tisdag": "Tu",
    "Onsdag": "We",
    "Torsdag": "Th",
    "Fredag": "Fr",
    "Lördag": "Sa",
    "Söndag": "Su",
}
DAYS_SI = {
    "po": "Mo",
    "Pon": "Mo",
    "to": "Tu",
    "Tor": "Tu",
    "sr": "We",
    "Sre": "We",
    "če": "Th",
    "Čet": "Th",
    "pe": "Fr",
    "Pet": "Fr",
    "so": "Sa",
    "Sob": "Sa",
    "ne": "Su",
    "Ned": "Su",
}
DAYS_IT = {
    "Lunedì": "Mo",
    "Lunedi": "Mo",
    "Lun": "Mo",
    "Lu": "Mo",
    "Martedì": "Tu",
    "Martedi": "Tu",
    "Mar": "Tu",
    "Ma": "Tu",
    "Mercoledì": "We",
    "Mercoledi": "We",
    "Mer": "We",
    "Me": "We",
    "Giovedì": "Th",
    "Giovedi": "Th",
    "Gio": "Th",
    "Gi": "Th",
    "Venerdì": "Fr",
    "Venerdi": "Fr",
    "Ven": "Fr",
    "Ve": "Fr",
    "Sabato": "Sa",
    "Sab": "Sa",
    "Sa": "Sa",
    "Domenica": "Su",
    "Dom": "Su",
    "Do": "Su",
}
DAYS_FR = {
    "Lu": "Mo",
    "Ma": "Tu",
    "Me": "We",
    "Je": "Th",
    "Ve": "Fr",
    "Sa": "Sa",
    "Di": "Su",
    "Lundi": "Mo",
    "Mardi": "Tu",
    "Mercredi": "We",
    "Jeudi": "Th",
    "Vendredi": "Fr",
    "Samedi": "Sa",
    "Dimanche": "Su",
}
DAYS_NL = {
    "Ma": "Mo",
    "Di": "Tu",
    "Wo": "We",
    "Do": "Th",
    "Vr": "Fr",
    "Za": "Sa",
    "Zo": "Su",
    "Maandag": "Mo",
    "Dinsdag": "Tu",
    "Woensdag": "We",
    "Donderdag": "Th",
    "Vrijdag": "Fr",
    "Zaterdag": "Sa",
    "Zondag": "Su",
}
DAYS_PL = {
    "Pn": "Mo",
    "Po": "Mo",
    "Wt": "Tu",
    "Śr": "We",
    "Cz": "Th",
    "Pt": "Fr",
    "Pi": "Fr",
    "Sb": "Sa",
    "So": "Sa",
    "Nd": "Su",
    "Ni": "Su",
}
DAYS_PT = {
    # "Se": "Mo",
    "Te": "Tu",
    # "Qu": "We",
    # "Qu": "Th",
    # "Se": "Fr",
    "Sa": "Sa",
    "Sá": "Sa",
    "Do": "Su",
}
DAYS_SK = {
    "Po": "Mo",
    "Ut": "Tu",
    "St": "We",
    "Št": "Th",
    "Pi": "Fr",
    "So": "Sa",
    "Ne": "Su",
}
DAYS_RU = {
    "Пн": "Mo",
    "Понедельник": "Mo",
    "Вт": "Tu",
    "Вторник": "Tu",
    "Ср": "We",
    "Среда": "We",
    "Чт": "Th",
    "Четверг": "Th",
    "Пт": "Fr",
    "Пятница": "Fr",
    "Сб": "Sa",
    "Суббота": "Sa",
    "Вс": "Su",
    "Воскресенье": "Su",
}
DAYS_RS = {
    "Ponedeljak": "Mo",
    "Utorak": "Tu",
    "Sreda": "We",
    "Četvrtak": "Th",
    "Petak": "Fr",
    "Subota": "Sa",
    "Nedelja": "Su",
}
DAYS_NO = {
    "Mandag": "Mo",
    "Måndag": "Mo",
    "Man": "Mo",
    "Tirsdag": "Tu",
    "Tysdag": "Tu",
    "Onsdag": "We",
    "Torsdag": "Th",
    "Tors": "Th",
    "Fredag": "Fr",
    "Fre": "Fr",
    "Lørdag": "Sa",
    "Laurdag": "Sa",
    "Lør": "Sa",
    "Søndag": "Su",
    "Sundag": "Su",
    "Søn": "Su",
}
DAYS_DK = {
    "Mandag": "Mo",
    "Man": "Mo",
    "Ma": "Mo",
    "Tirsdag": "Tu",
    "Ti": "Tu",
    "Onsdag": "We",
    "On": "We",
    "Torsdag": "Th",
    "Tors": "Th",
    "To": "Th",
    "Fredag": "Fr",
    "Fre": "Fr",
    "Fr": "Fr",
    "Lørdag": "Sa",
    "Lør": "Sa",
    "Lø": "Sa",
    "Søndag": "Su",
    "Søn": "Su",
    "So": "Su",
}
DAYS_FI = {
    "Maanantai": "Mo",
    "Ma": "Mo",
    "Tiistai": "Tu",
    "Ti": "Tu",
    "Keskiviikko": "We",
    "Ke": "We",
    "Torstai": "Th",
    "To": "Th",
    "Perjantai": "Fr",
    "Pe": "Fr",
    "Lauantai": "Sa",
    "La": "Sa",
    "Sunnuntai": "Su",
    "Su": "Su",
}
DAYS_ES = {
    "Lunes": "Mo",
    "Lun": "Mo",
    "Lu": "Mo",
    "Martes": "Tu",
    "Mar": "Tu",
    "Ma": "Tu",
    "Miercoles": "We",
    "Miércoles": "We",
    "Mie": "We",
    "Mié": "We",
    "Mi": "We",
    "Jueves": "Th",
    "Jue": "Th",
    "Ju": "Th",
    "Viernes": "Fr",
    "Vie": "Fr",
    "Vi": "Fr",
    "Sabado": "Sa",
    "Sábado": "Sa",
    "Sab": "Sa",
    "Sáb": "Sa",
    "Sa": "Sa",
    "Domingo": "Su",
    "Dom": "Su",
    "Do": "Su",
}

DAYS_RO = {
    "Luni": "Mo",
    "Marți": "Tu",
    "Miercuri": "We",
    "Joi": "Th",
    "Vineri": "Fr",
    "Sâmbătă": "Sa",
    "Duminică": "Su",
}

NAMED_DAY_RANGES_EN = {
    "Daily": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "All days": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "Weekdays": ["Mo", "Tu", "We", "Th", "Fr"],
    "Weekends": ["Sa", "Su"],
}

NAMED_DAY_RANGES_DK = {
    "Hverdage": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],  # Weekdays
}

NAMED_DAY_RANGES_RU = {
    "Ежедневно": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],  # Daily
    "По будням": ["Mo", "Tu", "We", "Th", "Fr"],  # Weekdays
    "По выходным": ["Sa", "Su"],  # Weekends
}

DELIMITERS_EN = {
    "-",
    "–",
    "—",
    "―",
    "‒",
    "to",
    "and",
    "from",
    "thru",
    "through",
}

DELIMITERS_ES = {
    "-",
    "a",
    "y",
    "de",
}


def day_range(start_day, end_day):
    start_ix = DAYS.index(sanitise_day(start_day))
    end_ix = DAYS.index(sanitise_day(end_day))
    if start_ix <= end_ix:
        return DAYS[start_ix : end_ix + 1]
    else:
        return DAYS[start_ix:] + DAYS[: end_ix + 1]


def sanitise_day(day: str, days: {} = DAYS_EN) -> str:
    if day is None:
        return None

    day = day.strip("-.\t ").lower()

    day = day.replace("https://", "").replace("http://", "").replace("schema.org/", "").title()

    if "#" in day:
        day = day.split("#", 1)[1]

    return days.get(day)


class OpeningHours:
    def __init__(self):
        self.day_hours = defaultdict(set)

    def add_days_range(self, days: [str], open_time, close_time, time_format="%H:%M"):
        for day in days:
            self.add_range(day, open_time, close_time, time_format=time_format)

    def add_range(self, day, open_time, close_time, time_format="%H:%M"):
        day = sanitise_day(day)

        if day not in DAYS:
            raise ValueError(f"day must be one of {DAYS}, not {day!r}")

        if not open_time or not close_time:
            return
        if isinstance(open_time, str):
            if open_time.lower() == "closed":
                return
        if isinstance(close_time, str):
            if close_time.lower() == "closed":
                return
            if close_time == "24:00" or close_time == "00:00":
                close_time = "23:59"
        if not isinstance(open_time, time.struct_time):
            open_time = time.strptime(open_time, time_format)
        if not isinstance(close_time, time.struct_time):
            close_time = time.strptime(close_time, time_format)

        self.day_hours[day].add((open_time, close_time))

    def as_opening_hours(self) -> str:
        day_groups = []
        this_day_group = None

        for day in DAYS:
            hours = ",".join(
                "%s-%s"
                % (
                    time.strftime("%H:%M", h[0]),
                    time.strftime("%H:%M", h[1]).replace("23:59", "24:00"),
                )
                for h in sorted(self.day_hours[day])
            )

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-24:00",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if not day_group["hours"]:
                    continue
                elif day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def from_linked_data(self, linked_data, time_format: str = "%H:%M"):
        if linked_data.get("openingHoursSpecification"):
            for rule in linked_data["openingHoursSpecification"]:
                if not rule.get("dayOfWeek") or not rule.get("opens") or not rule.get("closes"):
                    continue

                days = rule["dayOfWeek"]
                if not isinstance(days, list):
                    days = [days]

                for day in days:
                    self.add_range(
                        day=day,
                        open_time=rule["opens"],
                        close_time=rule["closes"],
                        time_format=time_format,
                    )
        elif linked_data.get("openingHours"):
            rules = linked_data["openingHours"]
            if not isinstance(rules, list):
                rules = re.findall(
                    r"((\w{2,3}|\w{2,3}\s?\-\s?\w{2,3}|(\w{2,3},)+\w{2,3})\s(\d\d:\d\d)\s?\-\s?(\d\d:\d\d))",
                    rules,
                )
                rules = [r[0] for r in rules]

            for rule in rules:
                if not rule:
                    continue
                days, time_ranges = rule.split(" ", 1)

                if "-" not in time_ranges:
                    continue

                for time_range in time_ranges.split(","):
                    start_time, end_time = time_range.split("-")

                    start_time = start_time.strip()
                    end_time = end_time.strip()

                    if "-" in days:
                        start_day, end_day = days.split("-")

                        start_day = sanitise_day(start_day)
                        end_day = sanitise_day(end_day)

                        for day in day_range(start_day, end_day):
                            self.add_range(day, start_time, end_time, time_format)
                    else:
                        for day in days.split(","):
                            if d := sanitise_day(day):
                                self.add_range(d, start_time, end_time, time_format)

    def add_ranges_from_string(
        self, ranges_string, days=DAYS_EN, named_day_ranges=NAMED_DAY_RANGES_EN, delimiters=DELIMITERS_EN
    ):
        # Build two regular expressions--one for extracting 12h
        # opening hour information, and one for extracting 24h
        # opening hour information from a supplied string.
        days_regex = r"(?:"
        days_regex_parts = []

        # Build delimiters regular expression.
        delimiter_regex = r"\s*(?:"
        delimiter_regex_parts = []
        for delimiter in delimiters:
            delimiter_regex_parts.append(re.escape(delimiter))
        delimiter_regex = delimiter_regex + r"|".join(delimiter_regex_parts) + r")\s*"

        # For each day of the week, create a list of synonyms.
        day_synonyms = defaultdict(list)
        for synonym, day in sorted(days.items()):
            day_synonyms[day].append(re.escape(synonym))

        # Assuming a week starts on Monday (most opening hours are
        # listed as such due to business vs. weekend hours), create
        # a regular expression of all day ranges possible in the
        # week starting Monday (or later).
        for i in range(0, 6, 1):
            start_day_string = r"(?<!\w)(" + r"|".join(day_synonyms[DAYS[i]]) + r")(?!\w)"
            end_days = []
            for j in range(i + 1, 7, 1):
                end_days.append("|".join(day_synonyms[DAYS[j]]))
            end_days_string = r"(?<!\w)(" + r"|".join(end_days) + r")(?!\w)"
            days_regex_parts.append(start_day_string + delimiter_regex + end_days_string)

        # Some sources will have a week start on Sunday and will
        # express day ranges as Sunday to Thursday (for example).
        # Create a regular expression to capture these day ranges
        # that commence on Sunday.
        start_day_string = r"(?<!\w)(" + r"|".join(day_synonyms["Su"]) + r")(?!\w)"
        end_days = []
        for j in range(0, 6, 1):
            end_days.append("|".join(day_synonyms[DAYS[j]]))
        end_days_string = r"(?<!\w)(" + r"|".join(end_days) + r")(?!\w)"
        days_regex_parts.append(start_day_string + delimiter_regex + end_days_string)

        # Create a regular expression for named day ranges.
        named_day_range_regex = r"(?<!\w)(" + r"|".join(named_day_ranges.keys()) + r")(?!\w)"
        days_regex_parts.append(named_day_range_regex)

        # Create a regular expression for single days of the week.
        single_days_regex = r"(?<!\w)(" + r"|".join(days.keys()) + r")(?!\w)"
        days_regex_parts.append(single_days_regex)

        # Compile regular expression parts together to create the
        # two regular expressions.
        days_regex = days_regex + r"|".join(days_regex_parts) + r")"
        time_regex_12h = r"(?<!\d)(\d(?!\d)|0\d|1[012])(?:(?:[:\.]?([0-5]\d))(?:[:\.]?[0-5]\d)?)?\s*([AP]M)?(?!\d)"
        time_regex_24h = r"(?<!\d)(\d(?!\d)|[01]\d|2[0-4])(?:[:\.]?([0-5]\d))(?:[:\.]?[0-5]\d)?(?!(?:\d|[AP]M))"
        full_regex_12h = (
            days_regex + r"(?:\W+|" + delimiter_regex + r")" + time_regex_12h + delimiter_regex + time_regex_12h
        )
        full_regex_24h = (
            days_regex + r"(?:\W+|" + delimiter_regex + r")" + time_regex_24h + delimiter_regex + time_regex_24h
        )

        # Execute both regular expressions.
        results_12h = re.findall(full_regex_12h, ranges_string, re.IGNORECASE)
        results_24h = re.findall(full_regex_24h, ranges_string, re.IGNORECASE)

        # Normalise results to 24h time.
        results_normalised = []
        if len(results_24h) > 0:
            # Parse 24h opening hour information.
            for result in results_24h:
                time_start = result[-4] + ":" + result[-3]
                time_end = result[-2] + ":" + result[-1]
                start_and_end_days = list(filter(None, result[:-4]))
                results_normalised.append([start_and_end_days, time_start, time_end])
        elif len(results_12h) > 0:
            # Parse 12h opening hour information.
            for result in results_12h:
                time_start = result[-6] + ":"
                if result[-5]:
                    time_start = time_start + result[-5]
                else:
                    time_start = time_start + "00"
                if result[-4]:
                    time_start = time_start + result[-4].upper()
                else:
                    # If AM/PM is not specified, it is almost always going to be AM for start times.
                    time_start = time_start + "AM"
                time_start_24h = time.strptime(time_start, "%I:%M%p")
                time_start_24h = time.strftime("%H:%M", time_start_24h)
                time_end = result[-3] + ":"
                if result[-2]:
                    time_end = time_end + result[-2]
                else:
                    time_end = time_end + "00"
                if result[-1]:
                    time_end = time_end + result[-1].upper()
                else:
                    # If AM/PM is not specified, it is almost always going to be PM for end times.
                    time_end = time_end + "PM"
                time_end_24h = time.strptime(time_end, "%I:%M%p")
                time_end_24h = time.strftime("%H:%M", time_end_24h)
                start_and_end_days = list(filter(None, result[:-6]))
                results_normalised.append([start_and_end_days, time_start_24h, time_end_24h])

        # Add ranges to OpeningHours object from normalised results.
        for result in results_normalised:
            if len(result[0]) == 1:
                if result[0][0].title() in named_day_ranges.keys():
                    day_list = named_day_ranges[result[0][0].title()]
                else:
                    day_list = [days[result[0][0].title()]]
            else:
                start_day = days[result[0][0].title()]
                end_day = days[result[0][1].title()]
                day_list = day_range(start_day, end_day)
            for day in day_list:
                self.add_range(day, result[1], result[2])
