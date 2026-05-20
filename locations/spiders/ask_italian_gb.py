import json
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AskItalianGBSpider(SitemapSpider, StructuredDataSpider):
    name = "ask_italian_gb"
    item_attributes = {"brand": "ASK Italian", "brand_wikidata": "Q4807056"}
    sitemap_urls = ["https://www.askitalian.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"/italian-restaurants/[^/]+/(?!menus|news|offers|poi|group)[^/]+(?:/(?!menus|news|offers|poi|group)[^/]+)?$",
            "parse_sd",
        )
    ]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        raw = response.xpath('//script[@type="application/ld+json" and @id="schema-restaurant"]/text()').get()
        if raw:
            yield json.loads(raw)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.RESTAURANT, item)
        yield item
