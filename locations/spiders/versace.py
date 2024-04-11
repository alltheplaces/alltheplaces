from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class VersaceSpider(Spider):
    name = "versace"
    item_attributes = {"brand": "Versace", "brand_wikidata": "Q696376"}
    allowed_domains = ["www.versace.com"]
    start_urls = ["https://www.versace.com/on/demandware.store/Sites-US-Site/en_US/Stores-Search"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["street_address"] = ", ".join(filter(None, [location.get("address1"), location.get("address2")]))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location.get("storeHours"))
            yield item
