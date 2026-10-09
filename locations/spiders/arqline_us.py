import json
import re
from collections import Counter
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response, TextResponse
from twisted.python.failure import Failure

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.linked_data_parser import LinkedDataParser


class ArqlineUSSpider(JSONBlobSpider):
    name = "arqline_us"
    item_attributes = {"operator": "Arqline"}
    shared_sites: set[str]

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://arqline.com/", callback=self.parse_home)

    def parse_home(self, response: Response) -> Iterable[Request]:
        yield response.follow(response.xpath('//script[@type="module"]/@src').get(), callback=self.parse)

    def extract_json(self, response: TextResponse) -> list[dict]:
        properties = json.loads(re.search(r"JSON\.parse\(`(\[\{\"id\".+?\])`\)", response.text).group(1))
        # A site shared by several buildings only describes one of them
        self.shared_sites = {
            site for site, count in Counter(prop["marketingSite"] for prop in properties).items() if count > 1
        }
        return properties

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature | Request]:
        item["website"] = feature["marketingSite"]
        item["image"] = response.urljoin(feature["images"][0])
        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)
        if item["website"] in self.shared_sites:
            yield item
        else:
            yield Request(
                item["website"],
                callback=self.parse_property,
                errback=self.errback_property,
                cb_kwargs={"item": item},
            )

    def parse_property(self, response: Response, item: Feature) -> Iterable[Feature]:
        # Most sites serve a JS bot check instead of the page; keep the listing data for those
        if ld := LinkedDataParser.find_linked_data(response, "LocalBusiness"):
            ld_item = LinkedDataParser.parse_ld(ld)
            for key in ("lat", "lon", "street_address", "postcode", "phone"):
                if ld_item.get(key):
                    item[key] = ld_item[key]
        yield item

    def errback_property(self, failure: Failure) -> Iterable[Feature]:
        yield failure.request.cb_kwargs["item"]
