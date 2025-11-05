from typing import AsyncIterator

from scrapy.http import Request

from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class BoscovsUSSpider(KiboSpider):
    name = "boscovs_us"
    item_attributes = {"brand": "Boscov's", "brand_wikidata": "Q4947190"}
    start_urls = ["https://www.boscovs.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    custom_settings = {"COOKIES_ENABLED": True, "USER_AGENT": BROWSER_DEFAULT}

    # A session cookie needs to be obtained prior to the Kibo Storefront API being used
    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.boscovs.com/", self.parse_cookie_page)

    def parse_cookie_page(self, response):
        for url in self.start_urls:
            yield Request(url, self.parse)

    def parse_item(self, item, location: {}, **kwargs):
        # Returned data often contains unwanted tab characters
        for field in "street_address", "city", "state", "email":
            if field in item:
                item[field] = item[field].replace("\t", "")
        for attribute in location["attributes"]:
            if attribute["fullyQualifiedName"] == "tenant~location-url":
                item["website"] = attribute["values"][0]
        yield item
