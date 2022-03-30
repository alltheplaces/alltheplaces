# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class SupervaluSpider(scrapy.Spider):
    name = "supervalu"
    item_attributes = {"brand": "SuperValu"}
    allowed_domains = ["www.supervalustores.com"]

    def start_requests(self):
        url = "http://www.supervalustores.com/tools/cm?getAll=cities"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        stores = response.json()
        for store in stores:
            hours = self.hours(store["hours"])
            yield GeojsonPointItem(
                city=store["city"],
                ref=store["id"],
                lat=store["lat"],
                lon=store["lng"],
                name=store["name"],
                phone=store["phone"],
                postcode=store["zip"],
                state=store["state"],
                addr_full=store["street"],
                opening_hours=store["hours"],
            )

    def hours(self, hours_string):
        """Returns a string of the store hours in a opening_hours format. If not able to parse, just returns the hours.
        Args: hours_string - A string of the store hours"""
        if "April" in hours_string:  # Edge case 1
            return hours_string.replace("<br />", "")

        if "Christmas" in hours_string:  # Edge case 2
            return hours_string.replace("<br />", "")

        if "Daily" in hours_string:
            if "Open 24 Hours Daily" in hours_string:
                return "24/7"

            elif "Winter" in hours_string or "Summer" in hours_string:
                season1, season1_hours, season2, season2_hours = hours_string.split(
                    "<br />"
                )
                days = "Mo-Su"
                season_1 = season1.strip()
                season2 = season2.strip()
                season1_hour_index = season1_hours.index("Daily")
                season2_hour_index = season2_hours.index("Daily")
                season1_hours = season1_hours[:season1_hour_index]
                season1_hours = self.to_24hr(season1_hours)
                season2_hours = self.to_24hr(season2_hours[:season2_hour_index])
                return days + " " + season1_hours + "; " + " || " + season2_hours + ";"

            elif "6 am to Midnight Daily" in hours_string:
                return "Mo-Su 6:00-00:00;"

            elif "CST" in hours_string:
                hours_string = hours_string.replace("CST", "")

            elif "Midnight" in hours_string:
                hours_string = hours_string.replace("Midnight", "0:00")

            days = "Mo-Su"
            hour_index = hours_string.index("Daily")
            hours = hours_string[:hour_index].strip()
            hours = self.to_24hr(hours)
            return days + " " + hours + ";"

        elif "7 days a week" in hours_string:
            days = "Mo-Su"
            reg_hours, seasonal_info = hours_string.split("<br />", 1)
            reg_hours = reg_hours.replace("7 days a week", "")
            reg_hours = self.to_24hr(reg_hours)
            season, season_hours = seasonal_info.split(":")
            season_hours = self.to_24hr(season_hours)
            return (
                days
                + " "
                + reg_hours
                + "; "
                + "|| "
                + "seasonal="
                + season
                + " "
                + season_hours
                + ";"
            )

        elif "<br />" in hours_string:
            if "spring hours" in hours_string:
                hours_string = hours_string.replace("(spring hours)", "").replace(
                    "(fall hours)", ""
                )
                days, spring_hours, fall_hours, sunday = hours_string.split("<br />")
                days = self.day_to_abbrev(days)
                spring_hours = self.to_24hr(spring_hours)
                fall_hours = self.to_24hr(fall_hours)
                su, sunday_hours = sunday.split(":")
                su = self.day_to_abbrev(su)
                sunday_hours = self.to_24hr(sunday_hours)
                return (
                    days
                    + " "
                    + spring_hours
                    + "; || "
                    + fall_hours
                    + "; "
                    + su
                    + " "
                    + sunday_hours
                )

            if "Closed Sundays" in hours_string:
                hours_string = hours_string.replace("<br />Closed Sundays", "")
                day1, day2 = hours_string.split("<br />", 1)
                wk_days, wk_hrs = day1.split(":")
                sat, sat_hrs = day2[:3], day2[3:]
                wk_days = self.day_to_abbrev(wk_days)
                wk_hrs = self.to_24hr(wk_hrs)
                sat = self.day_to_abbrev(sat)
                sat_hrs = self.to_24hr(sat_hrs)
                return wk_days + " " + wk_hrs + "; " + sat + " " + sat_hrs

            store_hours = ""
            for hours_info in hours_string.split("<br />"):  # day is 'day: hr'
                days, hours = hours_info.split(":", 1)
                days = self.day_to_abbrev(days)
                hours = self.to_24hr(hours)
                store_hours += days + " " + hours + "; "
            return store_hours

        elif hours_string == "":
            return hours_string

        elif "<br />" not in hours_string:
            if "Closed Sunday" in hours_string:
                return hours_string

            elif "Mon" not in hours_string:  # No open days given
                return self.to_24hr(hours_string)

            else:  # Like 'Mon-Fri: 7am - 8 pm; Sat: ...Sun:... ' no <br />
                try:  # Try to parse. If you can't just return
                    group1, group2, group3 = hours_string.split(";")
                    day1, hour1 = group1.split(":")
                    day2, hour2 = group2.split(":")
                    day3, hour3 = group3.split(":")
                    day1, day2, day3 = map(self.day_to_abbrev, (day1, day2, day3))
                    hour1, hour2, hour3 = map(self.to_24hr, (hour1, hour2, hour3))
                    return (
                        day1
                        + " "
                        + hour1
                        + "; "
                        + day2
                        + " "
                        + hour2
                        + "; "
                        + day3
                        + " "
                        + hour3
                        + "; "
                    )

                except ValueError:
                    return hours_string
        else:
            return hours_string  # If no idea how to parse. Just return the text

    def day_to_abbrev(self, days_string):
        """Converts a three letter abbreviation of days or range of days into open street map format. Ex. Mon-Fri -> Mo-Fri. Mon -> Mo."""
        days_string = days_string.strip()

        if "-" in days_string:
            day1, day2 = days_string.split("-")
            day1 = day1[:2]
            day2 = day2[:2]
            return day1 + "-" + day2

        else:
            return days_string[:2]

    def to_24hr(self, time_string):
        """Converts a time string from 12hr format to 24 hr format. Example 5 am - 7 pm -> 5:00-19:00"""

        def to_24(time, pm=False):
            """Helper Function. Converts a single time from 12 to 24. Ex. 7:30 pm -> 19:30"""
            if ":" in time:
                index = time.index(":")
                hour = time[:index]
                if pm:
                    if hour != "12":
                        hour = str(int(hour) + 12)
                time = hour + time[index:]
            else:
                if pm:
                    if time != "12":
                        time = str(int(time) + 12)
                time += ":00"
            return time

        pm1, pm2 = False, False
        time1, time2 = time_string.split("-", 1)
        new_times = ""

        if "pm" in time1:
            pm1 = True
        if "pm" in time2:
            pm2 = True

        time1 = time1.replace("am", "").replace("pm", "").strip()
        new_times += to_24(time1, pm=pm1)
        new_times += "-"

        time2 = time2.replace("am", "").replace("pm", "").strip()
        new_times += to_24(time2, pm=pm2)

        return new_times
