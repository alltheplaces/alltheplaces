import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FloorworldAUSpider(Spider):
    name = "floorworld_au"
    item_attributes = {"brand": "Floorworld", "brand_wikidata": "Q117156913"}
    allowed_domains = ["www.floorworld.com.au"]
    start_urls = ["https://www.floorworld.com.au/store-finder"]

    def parse(self, response):
        locations = chompjs.parse_js_object(
            response.xpath('(//div[contains(@class, "goto-next")]/following::script)/text()').get()
        )
        for location in locations:
            print(location)
            item = DictParser.parse(location)
            item["ref"] = location["hs_path"]
            if item.get("addr_full"):
                item["street_address"] = item.pop("addr_full").strip()
            item["state"] = location["state"]["name"]
            item["email"] = item["email"].strip()
            item["website"] = "https://www.floorworld.com.au/store-details/" + location["hs_path"]
            if location.get("store_facebook_url"):
                item["facebook"] = location["store_facebook_url"].split("?utm_campaign=", 1)[0]
            yield item
