from json import loads

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class VersaceSpider(Spider):
    name = "versace"
    item_attributes = {"brand": "Versace", "brand_wikidata": "Q696376"}
    allowed_domains = ["www.versace.com"]
    start_urls = ["https://www.versace.com/on/demandware.store/Sites-US-Site/en_US/Stores-Search"]
    user_agent = BROWSER_DEFAULT
    # TLS fingerprinting is used to detect bots, so Playwright must be used to
    # present a TLS fingerprint of a real web browser.
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False}
    is_playwright_spider = True

    def parse(self, response):
        # Playwright page responses for JSON data get wrapped in HTML.
        json_blob = loads(response.xpath("//pre/text()").get())
        for location in json_blob["stores"]:
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location.get("storeHours"))
            yield item
