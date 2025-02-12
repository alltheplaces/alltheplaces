import json
import re
from typing import Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature


class AmastyStoreLocatorSpider(Spider):
    """
    This store finder is provided as an extension either for Magento v1 or
    Magento v2. Some limited documentation on the store finder is provided as:
      v1: https://amasty.com/docs/doku.php?id=magento_1:store_locator
      v2: https://amasty.com/docs/doku.php?id=magento_2:store_locator

    To use this spider, specify one or more allowed_domain, and the default
    path /amlocator/index/ajax/ will be requested. If for some reason the path
    is not default, it can be overridden by supplying the full paths in
    start_urls.

    JSON dictionaries are returned but are highly variable in the quantity and
    type of fields within. Ther is often a popup_html field in the JSON
    dictionaries which contains HTML data relating to the feature and whilst
    some of this popup_html is parsed by default, often there are fields such
    as addresses and phone numbers that need to be manually extracted by
    overriding the pre_process_data and/or post_process_item functions of this
    spider.
    """

    def start_requests(self) -> Iterable[Request]:
        if len(self.start_urls) == 0:
            for domain in self.allowed_domains:
                yield Request(url=f"https://{domain}/amlocator/index/ajax/")
        else:
            for url in self.start_urls:
                yield Request(url=url)

    def parse(self, response: Response) -> Iterable[Feature]:
        raw_data = json.loads(re.search(r"items\":(\[.*\]),\"", response.text).group(1))
        yield from self.parse_features(raw_data)

    def parse_features(self, features: dict) -> Iterable[Feature]:
        for feature in features:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            if "popup_html" in feature and feature["popup_html"] is not None:
                popup_html = Selector(text=feature["popup_html"])
                if not item["name"]:
                    item["name"] = " ".join(
                        popup_html.xpath('//div[contains(@class, "amlocator-title")]//text()').get().split()
                    )
                links = popup_html.xpath('//a[contains(@class, "amlocator-link")]/@href').getall()
                for link in links:
                    if link.startswith("http") and not item["website"]:
                        item["website"] = link
                    elif link.startswith("tel:") and not item["phone"]:
                        item["phone"] = link
                    elif link.startswith("mailto:") and not item["email"]:
                        item["email"] = link
            else:
                popup_html = None
            yield from self.post_process_item(item, feature, popup_html)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
