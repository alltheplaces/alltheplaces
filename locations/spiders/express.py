from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class ExpressSpider(SitemapSpider, StructuredDataSpider):
    name = "express"
    item_attributes = {"brand": "Express", "brand_wikidata": "Q1384784"}
    sitemap_urls = [
        "https://stores.express.com/sitemap.xml",
        "https://stores.expressfactoryoutlet.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            if ld_obj.get("credentialSubject"):
                yield ld_obj["credentialSubject"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["image"] = None
        if "Closed" in item["name"]:
            set_closed(item)

        if branch := response.xpath("//title/text()").re_first(r" at (.+?) \|"):
            item["branch"] = branch

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
