import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class Take5USSpider(scrapy.Spider):
    name = "take_5_us"
    item_attributes = {"brand": "Take 5", "brand_wikidata": "Q112359190"}
    allowed_domains = ["www.take5.com"]
    start_urls = ["https://www.take5.com/page-data/locations/page-data.json"]

    def parse(self, response):
        for location in response.json()["result"]["pageContext"]["storeLocations"]:
            if location["is_active"] != 1:
                return
            item = DictParser.parse(location)
            item["ref"] = location["store_id"]
            item["lat"] = location["store_lat"]
            item["lon"] = location["store_long"]
            item["addr_full"] = location["geo_address"]
            item["street_address"] = location["store_address"]
            item["city"] = location["store_city"]
            item["state"] = location["store_state"]
            item["postcode"] = location["store_postcode"]
            item["phone"] = location["store_phone"]
            item["website"] = "https://www.take5.com" + location["path"]
            oh = OpeningHours()
            for day_name, day_times in location["hours"].items():
                if day_times["is_open"] != 1:
                    continue
                oh.add_range(day_name, day_times["open"], day_times["close"], "%I:%M %p")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
