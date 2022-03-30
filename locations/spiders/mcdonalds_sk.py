import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsSKSpider(scrapy.Spider):
    name = "mcdonalds_sk"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.sk"]

    start_urls = ("https://www.mcdonalds.sk/wp-content/themes/mcdonaldscz/rests.php",)

    def store_hours(self, data):
        day = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        day_groups = []
        this_day_group = {}
        day_hours = data.split(",")
        weekday = 0
        for day_hour in day_hours:
            hours = ""

            short_day = day[weekday]
            hours = day_hour.strip()
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

            weekday = weekday + 1

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
        stores = response.json()
        for store in stores:
            data = stores[store]
            properties = {
                "addr_full": data["address"],
                "city": data["city"],
                "ref": data["id"],
                "phone": data["tel"],
                "postcode": data["zip"],
                "name": data["restaurant_name"],
                "lat": data["lat"],
                "lon": data["lng"],
            }

            opening_hours = self.store_hours(data["worktime"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
