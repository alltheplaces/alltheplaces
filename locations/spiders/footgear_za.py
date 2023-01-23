from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FootgearZASpider(Spider):
    name = "footgear_za"
    item_attributes = {"brand": "Footgear", "brand_wikidata": "Q116290280"}
    start_urls = ["https://www.footgear.co.za/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = ", ".join(filter(None, [location.pop("address2"), location.pop("address")]))
            location["name"] = location.pop("store")

            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            hours = Selector(text=location["hours"] or "")
            for rule in hours.xpath("//tr"):
                day = rule.xpath("./td/text()").get()
                start_time, end_time = rule.xpath("./td/time/text()").get().split(" - ")
                item["opening_hours"].add_range(day, start_time, end_time)

            yield item
