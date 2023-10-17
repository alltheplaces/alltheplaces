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

# The below DAYS dicts are provided to be used with sanitise_day inorder for us to do best attempts at matching the
# given day into an English 2 char day to be used inside ATP and then to be exported to OSM formatted opening hours.

DAYS_AT = {"Mo": "Mo", "Di": "Tu", "Mi": "We", "Do": "Th", "Fr": "Fr", "Sa": "Sa", "So": "Su"}

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
    "Δευτέρα": "Mo",
    "Τρ": "Tu",
    "Τρίτη": "Tu",
    "Τε": "We",
    "Τετάρτη": "We",
    "Πέ": "Th",
    "Πέμπτη": "Th",
    "Πα": "Fr",
    "Παρασκευή": "Fr",
    "Σά": "Sa",
    "Σάββατο": "Sa",
    "Κυ": "Su",
    "Κυριακή": "Su",
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
    "Po": "Mo",
    "Pon": "Mo",
    "To": "Tu",
    "Tor": "Tu",
    "Sr": "We",
    "Sre": "We",
    "Če": "Th",
    "Čet": "Th",
    "Pe": "Fr",
    "Pet": "Fr",
    "So": "Sa",
    "Sob": "Sa",
    "Ne": "Su",
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
    "Pon": "Mo",
    "Poniedziałek": "Mo",
    "Wt": "Tu",
    "Wto": "Tu",
    "Wtorek": "Tu",
    "Śr": "We",
    "Sr": "We",
    "Sro": "We",
    "Śro": "We",
    "Środa": "We",
    "Cz": "Th",
    "Czw": "Th",
    "Czwartek": "Th",
    "Pt": "Fr",
    "Pi": "Fr",
    "Pia": "Fr",
    "Piątek": "Fr",
    "Sb": "Sa",
    "So": "Sa",
    "Sob": "Sa",
    "Sobota": "Sa",
    "Nd": "Su",
    "Ni": "Su",
    "Nie": "Su",
    "Niedz": "Su",
    "Niedzela": "Su",
    "Niedziela": "Su",
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

DAYS_SR = {
    "Pon": "Mo",
    "Ponedeljak": "Mo",
    "Ponediljak": "Mo",
    "Ponedjeljak": "Mo",
    "Понедељак": "Mo",
    "Понеделник": "Mo",
    "Uto": "Tu",
    "Utorak": "Tu",
    "Уторак": "Tu",
    "Sri": "We",
    "Sreda": "We",
    "Среда": "We",
    "Cet": "Th",
    "Čet": "Th",
    "Četvrtak": "Th",
    "Cetvrtak": "Th",
    "Четвртак": "Th",
    "Pet": "Fr",
    "Petak": "Fr",
    "Петак": "Fr",
    "Sub": "Sa",
    "Subota": "Sa",
    "Субота": "Sa",
    "Ned": "Su",
    "Nedelja": "Su",
    "Недеља": "Su",
}

NAMED_DAY_RANGES_DK = {
    "Hverdage": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],  # Weekdays
}

NAMED_DAY_RANGES_EN = {
    "Daily": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "All days": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "Weekdays": ["Mo", "Tu", "We", "Th", "Fr"],
    "Weekends": ["Sa", "Su"],
}

NAMED_TIMES_EN = {
    "Midday": ["12:00PM", "12:00"],
    "Midnight": ["12:00AM", "00:00"],
}

NAMED_DAY_RANGES_RU = {
    "Ежедневно": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],  # Daily
    "По будням": ["Mo", "Tu", "We", "Th", "Fr"],  # Weekdays
    "По выходным": ["Sa", "Su"],  # Weekends
}

DELIMITERS_EN = [
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
    "until",
]

DELIMITERS_ES = [
    "-",
    "a",
    "y",
    "de",
]

DELIMITERS_PL = [
    "-",
    "–",
    "—",
    "―",
    "‒",
    "od",
    "do",
]


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

    @staticmethod
    def delimiters_regex(delimiters: list[str] = DELIMITERS_EN) -> str:
        """
        Creates a regular expression for capturing delimiters within
        a string containing time information. For example, in the
        string of "Monday: 10am-2pm", ":" and "-" are both
        delimiters.
        :param delimiters: list of strings which are delimiters to
                           capture with the created regular
                           expression.
        :returns: regular expression which captures delimiters in a
                  string containing opening time information.
        """
        delimiter_regex = r"\s*(?:"
        delimiter_regex_parts = []
        for delimiter in delimiters:
            delimiter_regex_parts.append(re.escape(delimiter))
        delimiter_regex = delimiter_regex + r"|".join(delimiter_regex_parts) + r")\s*"
        return delimiter_regex

    @staticmethod
    def single_days_regex(days: dict = DAYS_EN) -> str:
        """
        Creates a regular expression for capturing single day names
        within a string containing time information. For example, in the
        string of "Monday: 9am-5pm", "Monday" is captured.
        :param days: dictionary mapping localised day names to those
                     within DAYS ("Mo", "Tu", ...).
        :returns: regular expression which captures single day names
                  in a string containing opening time information.
        """
        single_days_regex = r"(?<!\w)(" + r"|".join(map(re.escape, days.keys())) + r")(?!\w)"
        return single_days_regex

    @staticmethod
    def day_ranges_regex(days: dict = DAYS_EN, delimiters: list[str] = DELIMITERS_EN) -> list[str]:
        """
        Creates a list of regular expressions for capturing all
        combinations of day ranges, with wrap-around for ranges
        which wrap around both Monday and Sunday as the first days
        of a week. For example, a regular expression is created for
        capturing strings of "Mon-Sun", "Sun to Sat", "Tue and Wed".
        :param days: dictionary mapping localised day names to those
                     within DAYS ("Mo", "Tu", ...).
        :returns: list of regular expressions which capture day
                  ranges in a given string containing opening time
                  information.
        """
        # For each day of the week, create a list of synonyms.
        day_synonyms = defaultdict(list)
        for synonym, day in sorted(days.items()):
            day_synonyms[day].append(re.escape(synonym))

        # Assuming a week starts on Monday (most opening hours are
        # listed as such due to business vs. weekend hours), create
        # a regular expression of all day ranges possible in the
        # week starting Monday (or later).
        days_regex_parts = []
        for i in range(0, 6, 1):
            start_day_string = r"(?<!\w)(" + r"|".join(day_synonyms[DAYS[i]]) + r")(?!\w)"
            end_days = []
            for j in range(i + 1, 7, 1):
                end_days.append("|".join(day_synonyms[DAYS[j]]))
            end_days_string = r"(?<!\w)(" + r"|".join(end_days) + r")(?!\w)"
            days_regex_parts.append(start_day_string + OpeningHours.delimiters_regex(delimiters) + end_days_string)

        # Some sources will have a week start on Sunday and will
        # express day ranges as Sunday to Thursday (for example).
        # Create a regular expression to capture these day ranges
        # that commence on Sunday.
        start_day_string = r"(?<!\w)(" + r"|".join(day_synonyms["Su"]) + r")(?!\w)"
        end_days = []
        for j in range(0, 6, 1):
            end_days.append("|".join(day_synonyms[DAYS[j]]))
        end_days_string = r"(?<!\w)(" + r"|".join(end_days) + r")(?!\w)"
        days_regex_parts.append(start_day_string + OpeningHours.delimiters_regex(delimiters) + end_days_string)

        return days_regex_parts

    @staticmethod
    def named_day_ranges_regex(named_day_ranges: dict = NAMED_DAY_RANGES_EN) -> str:
        """
        Creates a regular expression for capturing named day ranges
        within a string containing time information. For example, in
        the string of "Weekends: 9am-5pm", "Weekends" is captured.
        :param named_day_ranges: dictionary mapping localised named
                                 day ranges to lists of days from
                                 DAYS ("Mo", "Tu", ...).
        :returns: regular expression which captures named day ranges
                  in a string containing opening time information.
        """
        named_day_ranges_regex = r"(?<!\w)(" + r"|".join(map(re.escape, named_day_ranges.keys())) + r")(?!\w)"
        return named_day_ranges_regex

    @staticmethod
    def replace_named_times(hours_string: str, named_times: dict = NAMED_TIMES_EN, time_24h: bool = True) -> str:
        """
        Replaces named times (e.g. Midnight) in a string with their
        12h equivalent (e.g. 12:00AM) or 24h equivalent (e.g 00:00).
        :param hours_string: string of opening hours information
                             containing named times.
        :param named_times: dictionary mapping localised named times
                            of day to a tuple of equivalent 24hr time
                            and 12hr time respectively.
        :param time_24h: boolean for whether the resulting string
                         should have named times replaced with 24h
                         or 12h time ranges.
        :returns: string with named times replaced with their 24h
                  equivalent or 12h equivalent times.
        """
        replaced_hours_string = hours_string
        if time_24h is True:
            for named_time_name, named_time_time in named_times.items():
                replaced_hours_string = (
                    replaced_hours_string.replace(named_time_name.lower(), named_time_time[1])
                    .replace(named_time_name.title(), named_time_time[1])
                    .replace(named_time_name.upper(), named_time_time[1])
                )
        else:
            for named_time_name, named_time_time in named_times.items():
                replaced_hours_string = (
                    replaced_hours_string.replace(named_time_name.lower(), named_time_time[0])
                    .replace(named_time_name.title(), named_time_time[0])
                    .replace(named_time_name.upper(), named_time_time[0])
                )
        return replaced_hours_string

    @staticmethod
    def time_of_day_regex(time_24h: bool = True) -> str:
        """
        Creates a regular expression for capturing times of day in
        either 24h or 12h notation.
        :param time_24h: boolean for whether the resulting regular
                         expression should capture 24h or 12h
                         opening time information.
        :returns: regular expression which captures times of day in
                  a string.
        """
        if time_24h is True:
            # Regular expression for extracting 24h times (e.g. 15:45)
            time_regex = (
                r"(?<!\d)(\d(?!\d)|[01]\d|2[0-4])(?:(?:[:\.]?([0-5]\d))(?:[:\.]?[0-5]\d)?)?(?!(?:\d|:|[AP]\.?M\.?))"
            )
        else:
            # Regular expression for extracting 12h times (e.g. 9:30AM)
            time_regex = r"(?<!\d)(\d(?!\d)|0\d|1[012])(?:(?:[:\.]?([0-5]\d))(?:[:\.]?[0-5]\d)?)?\s*([AP]\.?M\.?)?(?!(?:\d|:|[AP]\.?M\.?))"
        return time_regex

    @staticmethod
    def hours_extraction_regex(
        time_24h: bool = True,
        days: dict = DAYS_EN,
        named_day_ranges: dict = NAMED_DAY_RANGES_EN,
        delimiters: list[str] = DELIMITERS_EN,
    ) -> str:
        """
        Creates a regular expression for capturing opening time
        information from a localised string.
        :param time_24h: boolean for whether the resulting regular
                         expression should capture 24h or 12h
                         opening time information.
        :param days: dictionary mapping localised day names to those
                     within DAYS ("Mo", "Tu", ...).
        :param named_day_ranges: dictionary mapping localised named
                                 day ranges to lists of days from
                                 DAYS ("Mo", "Tu", ...).
        :param delimiters: list of strings which are delimiters to
                           capture with the created regular
                           expression.
        :returns: regular expression which can extract opening time
                  information from a string.
        """
        # Create a regular expression for capturing day names and
        # day ranges from within a string containing opening time
        # information. This regular expression is designed to
        # capture the following types of strings:
        #   Mon-Wed
        #   Tuesday to Thursday
        #   Saturday
        #   Weekends
        days_regex = r"(?:"
        days_regex_parts = OpeningHours.day_ranges_regex(days=days, delimiters=delimiters)
        days_regex_parts.append(OpeningHours.named_day_ranges_regex(named_day_ranges=named_day_ranges))
        days_regex_parts.append(OpeningHours.single_days_regex(days=days))
        days_regex = days_regex + r"|".join(days_regex_parts) + r")"

        full_regex = (
            days_regex
            + r"(?:\W+|"
            + OpeningHours.delimiters_regex(delimiters)
            + r")((?:(?:\s*,?\s*)?"
            + OpeningHours.time_of_day_regex(time_24h=time_24h)
            + OpeningHours.delimiters_regex(delimiters)
            + OpeningHours.time_of_day_regex(time_24h=time_24h)
            + r")+)"
        )
        return full_regex

    @staticmethod
    def days_in_day_range(
        day_range: list[str], days: dict = DAYS_EN, named_day_ranges: dict = NAMED_DAY_RANGES_EN
    ) -> list[str]:
        """ """
        day_list = []
        if len(day_range) == 1 or days[day_range[0].title()] == days[day_range[1].title()]:
            if day_range[0].title() in named_day_ranges.keys():
                day_list = named_day_ranges[day_range[0].title()]
            else:
                day_list = [days[day_range[0].title()]]
        elif len(day_range) == 2:
            start_day_index = DAYS.index(days[day_range[0].title()])
            end_day_index = DAYS.index(days[day_range[1].title()])
            if start_day_index > end_day_index:
                day_list = DAYS[start_day_index:] + DAYS[: end_day_index + 1]
            else:
                day_list = DAYS[start_day_index : end_day_index + 1]
        return day_list

    @staticmethod
    def extract_hours_from_string(
        ranges_string: str,
        days: dict = DAYS_EN,
        named_day_ranges: dict = NAMED_DAY_RANGES_EN,
        named_times: dict = NAMED_TIMES_EN,
        delimiters: list[str] = DELIMITERS_EN,
    ) -> list[tuple]:
        """
        Extracts opening time information from a localised string.
        For every day or day range in the localised string with an
        opening hours range supplied, this function will return a
        tuple containing a day/day range, an opening time, and
        closing time, all in a normalised format.
        :param ranges_string: localised string containing opening
                              time information.
        :param days: dictionary mapping localised day names to those
                     within DAYS ("Mo", "Tu", ...).
        :param named_day_ranges: dictionary mapping localised named
                                 day ranges to lists of days from
                                 DAYS ("Mo", "Tu", ...).
        :param named_times: dictionary mapping localised named times
                            of day to a tuple of equivalent 24hr time
                            and 12hr time respectively.
        :param delimiters: list of strings which are delimiters to
                           capture with the created regular
                           expression.
        :returns: list of tuples where each tuple has a list of days
                  at each end of a day range (e.g. ["Mon", "Sat"] or
                  a list containing a single ["Weekday"], an opening time in 24h notation and a
                  closing time in 24h notation.
        """
        # Create regular expressions for extracting opening time information from a string.
        hours_extraction_regex_24h = OpeningHours.hours_extraction_regex(
            time_24h=True, days=days, named_day_ranges=named_day_ranges, delimiters=delimiters
        )
        hours_extraction_regex_12h = OpeningHours.hours_extraction_regex(
            time_24h=False, days=days, named_day_ranges=named_day_ranges, delimiters=delimiters
        )

        # Replace named times in source ranges string (e.g. midnight -> 00:00).
        ranges_string_24h = OpeningHours.replace_named_times(ranges_string, named_times, True)
        ranges_string_12h = OpeningHours.replace_named_times(ranges_string, named_times, False)

        # Execute both regular expressions.
        results_24h = re.findall(hours_extraction_regex_24h, ranges_string_24h, re.IGNORECASE)
        if len(results_24h) == 0:
            results_12h = re.findall(hours_extraction_regex_12h, ranges_string_12h, re.IGNORECASE)

        # Normalise results to 24h time.
        results = []
        if len(results_24h) > 0:
            # Parse 24h opening hour information.
            for result in results_24h:
                time_start_index = result.index(next(filter(lambda x: len(x) > 0 and x[0].isdigit(), result)))
                day_range = list(filter(None, result[:time_start_index]))
                days_in_range = OpeningHours.days_in_day_range(
                    day_range=day_range, days=days, named_day_ranges=named_day_ranges
                )
                time_ranges = re.findall(
                    OpeningHours.time_of_day_regex(time_24h=True)
                    + OpeningHours.delimiters_regex(delimiters)
                    + OpeningHours.time_of_day_regex(time_24h=True),
                    result[time_start_index],
                    re.IGNORECASE,
                )
                for time_range in time_ranges:
                    time_start_minute = time_range[1]
                    if not time_range[1]:
                        time_start_minute = "00"
                    time_end_minute = time_range[3]
                    if not time_range[3]:
                        time_end_minute = "00"
                    results.append(
                        (days_in_range, f"{time_range[0]}:{time_start_minute}", f"{time_range[2]}:{time_end_minute}")
                    )
        elif len(results_12h) > 0:
            # Parse 12h opening hour information.
            for result in results_12h:
                time_start_index = result.index(next(filter(lambda x: len(x) > 0 and x[0].isdigit(), result)))
                day_range = list(filter(None, result[:time_start_index]))
                days_in_range = OpeningHours.days_in_day_range(
                    day_range=day_range, days=days, named_day_ranges=named_day_ranges
                )
                time_ranges = re.findall(
                    OpeningHours.time_of_day_regex(time_24h=False)
                    + OpeningHours.delimiters_regex(delimiters)
                    + OpeningHours.time_of_day_regex(time_24h=False),
                    result[time_start_index],
                    re.IGNORECASE,
                )
                for time_range in time_ranges:
                    time_start_hour = time_range[0]
                    if time_start_hour == "00":
                        time_start_hour = "12"
                    if time_range[1]:
                        time_start = f"{time_start_hour}:{time_range[1]}"
                    else:
                        time_start = f"{time_start_hour}:00"
                    if time_range[2]:
                        time_start = f"{time_start}{time_range[2].upper()}".replace(".", "")
                    else:
                        # If AM/PM is not specified, it is almost always going to be AM for start times.
                        time_start = f"{time_start}AM"
                    time_start_24h = time.strptime(time_start, "%I:%M%p")
                    time_start_24h = time.strftime("%H:%M", time_start_24h)
                    time_end_hour = time_range[3]
                    if time_end_hour == "00":
                        time_end_hour = "12"
                    if time_range[4]:
                        time_end = f"{time_end_hour}:{time_range[4]}"
                    else:
                        time_end = f"{time_end_hour}:00"
                    if time_range[5]:
                        time_end = f"{time_end}{time_range[5].upper()}".replace(".", "")
                    else:
                        # If AM/PM is not specified, it is almost always going to be PM for end times.
                        time_end = f"{time_end}PM"
                    time_end_24h = time.strptime(time_end, "%I:%M%p")
                    time_end_24h = time.strftime("%H:%M", time_end_24h)
                    results.append((days_in_range, time_start_24h, time_end_24h))
        return results

    def add_ranges_from_string(
        self,
        ranges_string: str,
        days: dict = DAYS_EN,
        named_day_ranges: dict = NAMED_DAY_RANGES_EN,
        named_times: dict = NAMED_TIMES_EN,
        delimiters: list[str] = DELIMITERS_EN,
    ) -> None:
        """
        Adds opening hour information from a localised string.
        :param ranges_string: localised string containing opening
                              time information.
        :param days: dictionary mapping localised day names to those
                     within DAYS ("Mo", "Tu", ...).
        :param named_day_ranges: dictionary mapping localised named
                                 day ranges to lists of days from
                                 DAYS ("Mo", "Tu", ...).
        :param named_times: dictionary mapping localised named times
                            of day to a tuple of equivalent 24hr time
                            and 12hr time respectively.
        :param delimiters: list of strings which are delimiters to
                           capture with the created regular
                           expression.
        """
        # Extract opening time information from localised string.
        results = OpeningHours.extract_hours_from_string(
            ranges_string=ranges_string,
            days=days,
            named_day_ranges=named_day_ranges,
            named_times=named_times,
            delimiters=delimiters,
        )

        # Add ranges to OpeningHours object.
        for result in results:
            for day in result[0]:
                self.add_range(day, result[1], result[2])
