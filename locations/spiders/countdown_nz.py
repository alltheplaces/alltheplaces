from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class CountdownNZSpider(Spider):
    name = "countdown_nz"
    item_attributes = {"brand": "Countdown", "brand_wikidata": "Q5176845"}
    allowed_domains = ["api.cdx.nz"]
    start_urls = ["https://api.cdx.nz/site-location/api/v1/sites?latitude=-42&longitude=174&maxResults=10000"]
    user_agent = BROWSER_DEFAULT
    # TLS fingerprinting is used to detect bots, so Playwright must be used to
    # present a TLS fingerprint of a real web browser.
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False}
    is_playwright_spider = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        # Playwright page responses for JSON data get wrapped in HTML.
        json_blob = loads(response.xpath("//pre/text()").get())
        for location in json_blob["siteDetail"]:
            item = DictParser.parse(location["site"])
            if location["site"].get("email") == "null":
                item.pop("email", None)
            item["website"] = (
                "https://www.countdown.co.nz/store-finder/"
                + str(item["ref"])
                + "/"
                + item["city"].lower().replace(" ", "-").replace(",", "")
                + "/"
                + item["name"].lower().replace(" ", "-").replace(",", "")
            )
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if not location["tradingHours"][0].get(day_name.lower()):
                    continue
                item["opening_hours"].add_range(
                    day_name,
                    location["tradingHours"][0].get(day_name.lower())["startTime"],
                    location["tradingHours"][0].get(day_name.lower())["endTime"],
                    "%H:%M:%S",
                )
            yield item
