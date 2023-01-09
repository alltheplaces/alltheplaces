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
    "Tue": "Tu",
    "Tu": "Tu",
    "Wednesday": "We",
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
    "Пон": "Mo",
    "Пт": "Fr",
    "Пет": "Fr",
    "Съб": "Sa",
    "нед": "Su",
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
DAYS_HU = {
    "Hé": "Mo",
    "Ke": "Tu",
    "Sze": "We",
    "Csü": "Th",
    "Pé": "Fr",
    "Szo": "Sa",
    "Vas": "Su",
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
    "Lun": "Mo",
    "Mar": "Tu",
    "Mer": "We",
    "Gio": "Th",
    "Ven": "Fr",
    "Sab": "Sa",
    "Dom": "Su",
}
DAYS_FR = {
    "Lu": "Mo",
    "Ma": "Tu",
    "Me": "We",
    "Je": "Th",
    "Ve": "Fr",
    "Sa": "Sa",
    "Di": "Su",
}

DAYS_NL = {
    "Ma": "Mo",
    "Di": "Tu",
    "Wo": "We",
    "Do": "Th",
    "Vr": "Fr",
    "Za": "Sa",
    "Zo": "Su",
}


def day_range(start_day, end_day):
    start_ix = DAYS.index(start_day)
    end_ix = DAYS.index(end_day)
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

    def add_range(self, day, open_time, close_time, time_format="%H:%M"):
        day = sanitise_day(day)

        if day not in DAYS:
            raise ValueError(f"day must be one of {DAYS}, not {day!r}")

        if open_time is None or close_time is None:
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

    def as_opening_hours(self):
        day_groups = []
        this_day_group = None

        for day in DAYS:
            hours = ",".join(
                "%s-%s"
                % (
                    time.strftime("%H:%M", h[0]),
                    time.strftime("%H:%M", h[1]).replace("23:59", "24:00"),
                )
                for h in self.day_hours[day]
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

    def from_linked_data(self, linked_data, time_format="%H:%M"):
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
                days, time_ranges = rule.split(" ", 1)

                if time_ranges.lower() == "closed":
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
                            self.add_range(day, start_time, end_time, time_format)
