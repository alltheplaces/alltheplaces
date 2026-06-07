from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MondialtissusFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mondialtissus_fr"
    item_attributes = {
        "brand": "Mondial Tissus",
        "brand_wikidata": "Q17635288",
    }
    sitemap_urls = ["https://magasins.mondialtissus.fr/robots.txt"]
    sitemap_rules = [
        (r"/tissu-mercerie/[\w-]+/[\w\d]+", "parse"),
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}
    drop_attributes = {"facebook", "phone"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category({"shop": "fabric"}, item)
        yield item
