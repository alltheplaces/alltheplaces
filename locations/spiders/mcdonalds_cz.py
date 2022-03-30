import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsCZSpider(scrapy.Spider):
    name = "mcdonalds_cz"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.cz"]

    start_urls = ("https://www.mcdonalds.cz/wp-content/themes/mcdonaldscz/rests.php",)

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        data = data.split(",")
        index = 0
        for item in data:
            if index == 7:
                break
            short_day = weekdays[index]
            hours = item
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }
            index = index + 1

        day_groups.append(this_day_group)

        if not day_groups:
            return None

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        for index in results:
            data = results[index]
            properties = {
                "addr_full": data["address"],
                "city": data["city"],
                "name": data["restaurant_name"],
                "postcode": data["zip"],
                "phone": data["tel"],
                "ref": data["id"],
                "lon": data["lng"],
                "lat": data["lat"],
            }

            opening_hours = self.store_hours(data["worktime"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
