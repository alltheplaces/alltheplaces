import logging
from collections import defaultdict
import time


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


class OpeningHours(object):
    def __init__(self):
        self.day_hours = defaultdict(list)

    def add_range(self, day, open_time, close_time, time_format="%H:%M"):
        if day not in DAYS:
            raise ValueError("day must be one of " + ", ".join(DAYS))

        if open_time is None or close_time is None:
            return
        if open_time.lower() == "closed":
            return
        if close_time.lower() == "closed":
            return
        if close_time == "24:00" or close_time == "00:00":
            close_time = "23:59"
        if not isinstance(open_time, time.struct_time):
            open_time = time.strptime(open_time, time_format)
        if not isinstance(close_time, time.struct_time):
            close_time = time.strptime(close_time, time_format)

        self.day_hours[day].append((open_time, close_time))

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
        DAY_MAPPING = {
            "Mon": "Mo",
            "Tue": "Tu",
            "Wed": "We",
            "Thur": "Th",
            "Fri": "Fr",
            "Sat": "Sa",
            "Sun": "Su",
        }
        if linked_data.get("openingHoursSpecification"):
            for rule in linked_data["openingHoursSpecification"]:
                if (
                    not rule.get("dayOfWeek")
                    or not rule.get("opens")
                    or not rule.get("closes")
                ):
                    logging.warning("Skipping openingHoursSpecification rule")
                    continue

                days = []
                if not isinstance(rule["dayOfWeek"], list):
                    days.append(rule["dayOfWeek"])
                else:
                    days = rule["dayOfWeek"]
                for day in days:
                    day = (
                        day.replace("https://", "")
                        .replace("http://", "")
                        .replace("schema.org/", "")[0:2]
                        .title()
                    )

                    self.add_range(
                        day=day,
                        open_time=rule["opens"],
                        close_time=rule["closes"],
                        time_format=time_format,
                    )
        elif linked_data.get("openingHours"):
            rules = []
            if not isinstance(linked_data["openingHours"], list):
                rules.append(linked_data["openingHours"])
            else:
                rules = linked_data["openingHours"]

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
                        if start_day in DAY_MAPPING:
                            start_day = DAY_MAPPING[start_day]
                        if end_day in DAY_MAPPING:
                            end_day = DAY_MAPPING[end_day]
                        for i in range(DAYS.index(start_day), DAYS.index(end_day) + 1):
                            self.add_range(DAYS[i], start_time, end_time, time_format)
                    else:
                        for day in days.split(","):
                            if day in DAY_MAPPING:
                                day = DAY_MAPPING[day]
                            self.add_range(
                                day.strip(), start_time, end_time, time_format
                            )
