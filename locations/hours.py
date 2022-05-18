from collections import defaultdict
import time


DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class OpeningHours(object):
    def __init__(self):
        self.day_hours = defaultdict(list)

    def add_range(self, day, open_time, close_time, time_format="%H:%M"):
        if day not in DAYS:
            raise ValueError("day must be one of " + ", ".join(DAYS))

        if open_time.lower() == "closed":
            return
        if close_time.lower() == "closed":
            return
        if not isinstance(open_time, time.struct_time):
            open_time = time.strptime(open_time, time_format)
        if not isinstance(close_time, time.struct_time):
            close_time = time.strptime(close_time, time_format)

        self.day_hours[day].append((open_time, close_time))

    def as_opening_hours(self):
        day_groups = []
        this_day_group = None

        for day in DAYS:
            hours = " ".join(
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
