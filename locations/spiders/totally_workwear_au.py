from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TotallyWorkwearAUSpider(Spider):
    name = "totally_workwear_au"
    item_attributes = {"brand": "Totally Workwear", "brand_wikidata": "Q119247989"}
    allowed_domains = ["www.totallyworkwear.com.au"]
    start_urls = ["https://www.totallyworkwear.com.au/api/places"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["path"]
            item["lat"] = location["geometry"]["location"]["lat"]
            item["lon"] = location["geometry"]["location"]["lng"]
            item["phone"] = location["formatted_phone_number"]
            item["website"] = "https://www.totallyworkwear.com.au/store/" + location["path"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(" ".join(location["opening_hours"]["weekday_text"]))
            yield item
