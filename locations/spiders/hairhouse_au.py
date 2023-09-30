from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class HairhouseAUSpider(Spider):
    name = "hairhouse_au"
    item_attributes = {"brand": "Hairhouse", "brand_wikidata": "Q118383855"}
    allowed_domains = ["www.hairhouse.com.au"]
    start_urls = ["https://www.hairhouse.com.au/app/services/Store.Service.ss"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["location"]
            item["street_address"] = ", ".join(filter(None, [location["address1"], location["address2"]]))
            item["website"] = "https://www.hairhouse.com.au/stores/" + location["urlcomponent"]
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                day_abbrev = day[:3].lower()
                item["opening_hours"].add_range(
                    day, location[f"{day_abbrev}Start"], location[f"{day_abbrev}Ending"], "%I:%M %p"
                )
            yield item
