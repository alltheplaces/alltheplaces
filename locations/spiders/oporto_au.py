from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OportoAUSpider(Spider):
    name = "oporto_au"
    item_attributes = {"brand": "Oporto", "brand_wikidata": "Q4412342"}
    allowed_domains = ["www.oporto.com.au"]
    start_urls = ["https://www.oporto.com.au/api/stores/0/"]

    def parse(self, response):
        locations = response.json()
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["website"] = "https://www.oporto.com.au/locations/" + location["slug"] + "/"
            oh = OpeningHours()
            for day_name, hours in location["opening_hours"].items():
                if hours is False:
                    continue
                if hours is True:
                    hours = {"open": "00:00", "close": "23:59"}
                oh.add_range(day_name.title(), hours["open"], hours["close"])
            item["opening_hours"] = oh.as_opening_hours()
            yield item
