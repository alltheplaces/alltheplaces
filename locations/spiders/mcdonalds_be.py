import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBESpider(Spider):
    name = "mcdonalds_be"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.be"]
    start_urls = ["https://www.mcdonalds.be/en/restaurants/api/restaurants"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = re.sub(r"\(\s*(Drive|Mall|In-Store)\s*\)", "", item["name"], re.IGNORECASE).strip()
            item["housenumber"] = location.get("nr")
            item["street"] = location.get("street_en")
            item["city"] = location.get("city_en")
            item["lat"] = float(location["lat_times_a_million"]) / 1000000.0
            item["lon"] = float(location["lng_times_a_million"]) / 1000000.0
            item["website"] = item["extras"]["website:nl"] = "https://www.mcdonalds.be/{}/restaurants/{}".format(
                "nl", location["slug"]
            )
            item["extras"]["website:en"] = "https://www.mcdonalds.be/{}/restaurants/{}".format("en", location["slug"])
            item["extras"]["website:fr"] = "https://www.mcdonalds.be/{}/restaurants/{}".format("fr", location["slug"])

            item["opening_hours"] = OpeningHours()
            for day_hours in location["opening_hours"]:
                if day_hours["text"] == "24/24":
                    item["opening_hours"].add_range(day_hours["weekday"].title(), "00:00", "24:00")
                else:
                    item["opening_hours"].add_range(
                        day_hours["weekday"].title(),
                        day_hours["text"].split(" - ", 1)[0],
                        day_hours["text"].split(" - ", 1)[1],
                    )

            service_ids = [s["service_id"] for s in location["services"]]
            apply_yes_no(Extras.DRIVE_THROUGH, item, 2 in service_ids, False)
            apply_yes_no(Extras.DELIVERY, item, 15 in service_ids, False)
            apply_yes_no(Extras.WIFI, item, 1 in service_ids, False)

            yield item
