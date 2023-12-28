from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT

class WilliamsSonomaUSCASpider(Spider):
    name = "williams_sonoma_us_ca"
    item_attributes = {"brand": "Williams Sonoma", "brand_wikidata": "Q96415240"}
    allowed_domains = ["www.williams-sonoma.com"]
    start_urls = ["https://www.williams-sonoma.com/api/phygital/v1/storesbylocation.json?brands=WS&lat=40.71304703&lng=-74.00723267&radius=100000&includeOutlets=true"]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        # A quirk of scrapy-playwright is that the raw JSON response can't be
        # obtained as Playwright's Response object is not exposed. Instead, a
        # HTML wrapper is put around the raw JSON response, and thus we need
        # to extract from this HTML wrapper.
        for location in loads(response.xpath('//pre/text()').get()):
            item = DictParser.parse(location)
            item["street_address"] = location["address"].get("addrLine1")
            item["website"] = "https://www.williams-sonoma.com/stores/{}-{}".format(location["address"].get("countryCode").lower(), location["storeIdentifier"])
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location.get("storeHoursMap", {}).items():
                if day_name.title() not in DAYS_FULL:
                    continue
                item["opening_hours"].add_range(day_name, *day_hours.split(" - ", 1), "%I:%M %p")
            yield item
