from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature

# Source code and some limited documentation for the Limesharp Store
# Locator (also known as "Stockists") is available from:
# https://github.com/motou/magento2-store-locator-stockists-extension
#
# To use this store finder, specify allowed_domains = [x, y, ..]
# (either one or more domains such as example.net) and the default
# path for the Limesharp Store Locator API endpoint will be used.
# In the event the default path is different, you can alternatively
# specify one or more start_urls = [x, y, ..].
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (an ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class LimesharpStoreLocatorSpider(Spider):
    def start_requests(self):
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                yield JsonRequest(url=f"https://{domain}/stockists/ajax/stores/")
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if (
                not location["name"]
                and not location["latitude"]
                and not location["longitude"]
                and not location["address"]
            ):
                continue
            item = DictParser.parse(location)
            item["ref"] = location["stockist_id"]
            item["street_address"] = location["address"]
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
