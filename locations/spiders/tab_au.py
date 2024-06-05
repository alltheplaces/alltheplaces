import re

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST


class TABAUSpider(Spider):
    name = "tab_au"
    item_attributes = {"brand": "TAB", "brand_wikidata": "Q110288149", "extras": Categories.SHOP_BOOKMAKER.value}
    allowed_domains = ["api.beta.tab.com.au"]
    start_urls = [
        "https://api.beta.tab.com.au/v1/venue-locator-service/public-venue-search?zoomLevel=19&topLeftLon=0&bottomRightLat=-90&bottomRightLon=-180&topLeftLat=0"
    ]
    user_agent = FIREFOX_LATEST  # Old user agent versions are blocked by the API (timeout).
    requires_proxy = "AU"

    def parse(self, response):
        for location in response.json()["venues"]:
            if location["status"] != "Active":
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street", None)
            if item["street_address"]:
                item["street_address"] = item["street_address"].strip()
            if item["postcode"]:
                item["postcode"] = str(item["postcode"])
            if item["phone"]:
                if re.match(r"^\d+\.\d+$", item["phone"]):
                    item.pop("phone", None)  # Invalid phone number.
            yield item
