from typing import Iterable

from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class NordstromRackSpider(SitemapSpider, StructuredDataSpider):
    name = "nordstrom_rack"
    item_attributes = {"brand": "Nordstrom Rack", "brand_wikidata": "Q21463374"}
    sitemap_urls = ["https://stores.nordstromrack.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.nordstromrack\.com\/\w{2}\/\w{2}\/[-\w]+\/[-.\w]+$",
            "parse",
        )
    ]
    drop_attributes = {"image", "email"}

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            if ld_obj.get("credentialSubject"):
                yield ld_obj["credentialSubject"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        name = item.pop("name")
        if name.startswith("Coming Soon"):
            return
        item["branch"] = name.removeprefix("Nordstrom Rack ").removeprefix("at ")
        item["website"] = response.url
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
