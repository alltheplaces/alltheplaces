from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ScsGBSpider(StructuredDataSpider):
    name = "scs_gb"
    item_attributes = {"brand": "ScS", "brand_wikidata": "Q19654399"}
    # https://www.scs.co.uk now redirects to https://www.poltronesofa.co.uk
    start_urls = ["https://www.poltronesofa.co.uk/stores/"]
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for link in response.xpath('//a[contains(@href, "/stores/")]/@href').getall():
            if link.endswith(".html"):
                yield response.follow(link, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("poltronesofà ")
        item["phone"] = item["phone"].removeprefix("Phone: ")
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
