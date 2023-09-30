from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TacoJohnsUSSpider(Spider):
    name = "taco_johns_us"
    item_attributes = {"brand": "Taco John's", "brand_wikidata": "Q7673962"}
    allowed_domains = ["locations.tacojohns.com"]
    start_urls = [
        "https://locations.tacojohns.com/modules/multilocation/?near_location=90210&threshold=50000&distance_unit=miles&limit=50000&services__in=&language_code=en-us&published=1&within_business=true"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["objects"]:
            if "COMING SOON" in location["location_name"].upper():
                continue
            item = DictParser.parse(location)
            item["name"] = location["location_name"]
            item["street_address"] = item.pop("street")
            item["addr_full"] = location["formatted_address"]
            item["phone"] = location["phones"][0]["e164"]
            item["website"] = location["location_url"]
            item["opening_hours"] = OpeningHours()
            for day_number, day_abbrev in enumerate(DAYS):
                for hours_range in list(filter(None, location["hours_of_operation"][day_number])):
                    item["opening_hours"].add_range(day_abbrev, hours_range[0], hours_range[1], "%H:%M:%S")
            apply_yes_no(Extras.DRIVE_THROUGH, item, "drive-thru" in location["services"], False)
            apply_yes_no(Extras.DELIVERY, item, "delivery" in location["services"], False)
            yield item
