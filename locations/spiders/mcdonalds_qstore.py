import scrapy
import re

from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsQStoreSpider(scrapy.Spider):
    name = "mcdonalds_qstore"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.com.au", "mcdonalds.co.nz", "mcdonalds.eg"]
    start_urls = (
        "https://mcdonalds.com.au/data/store",
        "https://mcdonalds.co.nz/data/store",
        "https://mcdonalds.eg/Stotes",
    )

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2}) ([ap.m]{2})", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2}) ([ap.m]{2})", time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p." else int(h),
            int(m),
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        day_hours = data["store_trading_hour"]
        for day_hour in day_hours:
            day, start, end = day_hour[0], day_hour[1], day_hour[2]
            if day == "Day":
                continue
            short_day = day[:2]
            hours = "{}:{}-{}:{}".format(start[:2], start[2:], end[:2], end[2:])
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
        def country_from_url(response):
            return response.url.split("/")[2].split(".")[-1].upper()

        for data in response.json():
            properties = {
                "city": data["store_suburb"],
                "ref": data["store_code"],
                "street_address": data["store_address"],
                "phone": data.get("store_phone"),
                "state": data["store_state"],
                "postcode": data.get("store_postcode"),
                "name": data["title"],
                "geolocation": data.get("lat_long"),
            }
            item = DictParser.parse(properties)
            item["country"] = country_from_url(response)

            # The alternative way of providing the location.
            coords = data.get("store_geocode")
            if coords and "," in coords:
                item["lat"] = coords.split(",")[1]
                item["lon"] = coords.split(",")[0]

            if not item["country"] == "EG":
                opening_hours = self.store_hours(data)
                if opening_hours:
                    item["opening_hours"] = opening_hours

            yield item
