import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsPLSpider(scrapy.Spider):
    name = "mcdonalds_pl"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["mcdonalds.pl"]

    start_urls = ("https://mcdonalds.pl/restauracje/getMarkers",)

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = {
            "1": "Mo",
            "2": "Th",
            "3": "We",
            "4": "Tu",
            "5": "Fr",
            "6": "Sa",
            "7": "Su",
        }

        for index in data:
            hours = ""

            short_day = weekdays[index]
            hours = "{}-{}".format(data[index]["from"], data[index]["to"])
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

        for item in results:
            properties = {
                "addr_full": item["address"],
                "city": item["city"],
                "name": "McDonald's",
                "postcode": item["postCode"],
                "phone": item["phone"],
                "ref": item["id"],
                "lon": item["lng"],
                "lat": item["lat"],
                "state": item["province"],
            }

            opening_hours = self.store_hours(item["hours"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
