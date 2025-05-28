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

    To use this spider, specify one or more `allowed_domain`, and the default
    path `/amlocator/index/ajax/` will be requested. If for some reason the
    path is not default, it can be overridden by supplying the full path in
    `start_urls`. Some implementations of Amasty Store Finder limit the number
    of features returned per request and then expect the client to browse
    through multiple pages of results. If this is the case for spider,
    additionally toggle `pagination_mode` to `True`.

    JSON dictionaries are returned but are highly variable in the quantity and
    type of fields within. Ther is often a `popup_html` field in the JSON
    dictionaries which contains HTML data relating to the feature and whilst
    some of this `popup_html` is parsed by default, often there are fields
    such as addresses and phone numbers that need to be manually extracted by
    overriding the `pre_process_data` and/or `post_process_item` functions of
    this spider.
    """
    # Public attributes. You may set these attributes in a spider.
    pagination_mode: bool = False

    # Private attributes. Do not set these attributes in a spider.
    _first_feature_id: int | None = None
    _crawl_completed: bool = False

    def start_requests(self) -> Iterable[Request]:
        headers = {
            "X-Requested-With": "XMLHttpRequest"
        }
        pagination_attribute = ""
        if self.pagination_mode:
            pagination_attribute = "?p=1"
        if len(self.start_urls) == 0:
            for domain in self.allowed_domains:
                yield Request(url=f"https://{domain}/amlocator/index/ajax/{pagination_attribute}", headers=headers, method="POST")
        else:
            for url in self.start_urls:
                yield Request(url=f"{url}{pagination_attribute}", headers=headers, method="POST")

    def parse(self, response: Response) -> Iterable[Feature | Request]:
        raw_data = json.loads(re.search(r"items\":(\[.*\]),\"", response.text).group(1))
        yield from self.parse_features(raw_data)

        if self.pagination_mode and not self._crawl_completed:
            # Continue the crawl by requesting the next page of features.
            print(response.url)
            if m := re.search(r"\?p=(\d+)$", response.url):
                next_page_number = int(m.group(1)) + 1
                next_page_url = re.sub(r"\?p=\d+$", f"?p={next_page_number}", response.url)
                headers = {
                    "X-Requested-With": "XMLHttpRequest"
                }
                yield Request(url=next_page_url, headers=headers, method="POST", dont_filter=True)

    def parse_features(self, features: dict) -> Iterable[Feature | Request]:
        for feature in features:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            if "popup_html" in feature and feature["popup_html"] is not None:
                popup_html = Selector(text=feature["popup_html"])
                if not item["name"]:
                    if feature_name := popup_html.xpath('//div[contains(@class, "amlocator-title")]//text()').get():
                        item["name"] = re.sub(r"\s+", " ", feature_name)
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
            if self.pagination_mode:
                if self._first_feature_id is None:
                    # Remember the first feature ID observed so that it can be
                    # used to determine when the last page of results has
                    # already been returned. After the last page of results
                    # has been returned, the API will just keep returning the
                    # first page of results for every higher page number.
                    self._first_feature_id = feature["id"]
                elif self._first_feature_id == feature["id"]:
                    # Stop the crawl as all features have been returned.
                    self._crawl_completed = True
                    return
            yield from self.post_process_item(item, feature, popup_html)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature | Request]:
        """Override with any post-processing on the item."""
        yield item
