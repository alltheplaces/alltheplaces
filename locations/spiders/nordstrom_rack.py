from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NordstromRackSpider(SitemapSpider, StructuredDataSpider):
    name = "nordstrom_rack"
    item_attributes = {"brand": "Nordstrom Rack", "brand_wikidata": "Q21463374"}
    sitemap_urls = ["https://stores.nordstromrack.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.nordstromrack\.com\/\w{2}\/\w{2}\/[-\w]+\/[-\w]+$",
            "parse",
        )
    ]
    drop_attributes = {"image"}
    wanted_types = ["Organization"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Nordstrom Rack ").removeprefix("at ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
