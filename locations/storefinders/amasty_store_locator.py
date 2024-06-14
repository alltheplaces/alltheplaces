from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser

# This store finder is provided as an extension either for Magento
# v1 or Magento v2. Some limited documentation on the store finder
# is provided as:
# v1: https://amasty.com/docs/doku.php?id=magento_1:store_locator
# v2: https://amasty.com/docs/doku.php?id=magento_2:store_locator
#
# To use this spider, specify one or more allowed_domain, and the
# default path /amlocator/index/ajax/ will be requested. If for
# some reason the path is not default, it can be overridden by
# supplying full paths in start_urls.
#
# JSON blobs of location are returned but are highly variable as
# to how many fields are provided. There is often a popup_html
# field in this JSON blob that contains HTML data relating to the
# location and whilst some of this is parsed by default, often there
# are fields such as addresses and phone numbers that need to be
# manually extracted by overriding the parse_item function of this
# store finder and then updating item fields using
# popup_html.xpath(...) queries.


class AmastyStoreLocatorSpider(Spider, AutomaticSpiderGenerator):
    detection_rules = [
        DetectionRequestRule(url=r"^https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/amlocator\/index\/ajax\/?"),
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)(?:\/[^\/]+)+\/amlocator\/index\/ajax\/?)$"
        ),
    ]

    def start_requests(self):
        if len(self.start_urls) == 0:
            for domain in self.allowed_domains:
                yield Request(url=f"https://{domain}/amlocator/index/ajax/")
        else:
            for url in self.start_urls:
                yield Request(url=url)

    def parse(self, response, **kwargs):
        yield from self.parse_items(response.json()["items"])

    def parse_items(self, items: [dict]):
        for location in items:
            item = DictParser.parse(location)
            if "popup_html" in location:
                popup_html = Selector(text=location["popup_html"])
                if not item["name"]:
                    item["name"] = " ".join(
                        popup_html.xpath('//div[contains(@class, "amlocator-title")]//text()').get().split()
                    )
                if not item["website"]:
                    item["website"] = popup_html.xpath('//a[contains(@class, "amlocator-link")]/@href').get()
            else:
                popup_html = None
            yield from self.parse_item(item, location, popup_html)

    def parse_item(self, item, location, popup_html):
        yield item

    def storefinder_exists(response: Response) -> bool | Request:
        # Example: https://www.aussiedisposals.com.au/store-locator/
        # Example: https://www.lcbo.com/en/stores/
        if response.xpath('//script[contains(text(), "/amlocator/index/ajax/")]/text()').get():
            return True

        return False

    def extract_spider_attributes(response: Response) -> dict | Request:
        return {
            "allowed_domains": [urlparse(response.url).netloc],
        }
