from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class JardilandSpider(Spider):
    name = "jardiland"
    item_attributes = {"brand": "Jardiland", "brand_wikidata": "Q3162276"}
    allowed_domains = ["api.jardiland.com"]
    start_urls = ["https://api.jardiland.com/store-locator/store"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = clean_address(location["address"]["road"])
            item["website"] = "https://www.jardiland.com/magasins/magasin-" + location["slug"]

            item["opening_hours"] = OpeningHours()
            for day_number, day_name in enumerate(DAYS):
                if (
                    not location.get("openingHours")
                    or not location["openingHours"].get("weeklySchedule")
                    or day_number >= len(location["openingHours"]["weeklySchedule"])
                ):
                    continue
                for day_hours in location["openingHours"]["weeklySchedule"][day_number]["schedule"]:
                    item["opening_hours"].add_range(day_name, day_hours["start"], day_hours["end"])

            yield item
