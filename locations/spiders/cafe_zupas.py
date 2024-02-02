import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class CafeZupasSpider(scrapy.Spider):
    name = "cafe_zupas"
    item_attributes = {"brand": "Café Zupas", "brand_wikidata": "Q123687995"}
    allowed_domains = ["cafezupas.com"]
    start_urls = ["https://cafezupas.com/server.php?url=https://api.controlcenter.zupas.com/api/markets/listing"]

    def parse_hours(self, location):
        opening_hours = OpeningHours()
        timings = [
            ["mon_thurs_timings_open", "mon_thurs_timings_close"],
            ["fri_sat_timings_open", "fri_sat_timings_close"],
        ]
        for i in timings:
            if location[i[0]] in ["Closed", ""] or location[i[1]] in ["Closed", ""]:
                continue
            # Monday - Thursday
            if i[0] == "mon_thurs_timings_open":
                day_group_1 = ["MO", "TU", "WE", "TH"]
                for day in day_group_1:
                    opening_hours.add_range(
                        day=day,
                        open_time=location[i[0]],
                        close_time=location[i[1]],
                        time_format="%I:%M %p",
                    )
            # Friday - Saturday
            if i[0] == "fri_sat_timings_open":
                day_group_2 = ["FR", "SA"]
                for day in day_group_2:
                    opening_hours.add_range(
                        day=day,
                        open_time=location[i[0]],
                        close_time=location[i[1]],
                        time_format="%I:%M %p",
                    )
        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()
        for i in data["data"]["data"]:
            for location in i["locations"]:
                properties = {
                    "ref": location["id"],
                    "website": "https://cafezupas.com/locationcopy/info/" + location["name"].lower().replace(" ", "-"),
                    "name": location["name"],
                    "image": "https://cafezupas.com" + location["image"] if location["image"] is not None else None,
                    "phone": location["phone"],
                    "lat": location["lat"],
                    "lon": location["long"],
                    "street_address": location["address"],
                    "city": location["city"],
                    "state": location["state"],
                    "postcode": location["zip"],
                    "facebook": location["facebook_url"],
                    "opening_hours": self.parse_hours(location),
                }
                yield Feature(**properties)
