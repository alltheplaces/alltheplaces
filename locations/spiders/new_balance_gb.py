from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NewBalanceGBSpider(SitemapSpider, StructuredDataSpider):
    name = "new_balance_gb"
    item_attributes = {"brand": "New Balance", "brand_wikidata": "Q742988"}
    sitemap_urls = ["https://stores.newbalance.co.uk/sitemap1.xml"]
    sitemap_rules = [(r"^https:\/\/stores\.newbalance\.co\.uk\/[\w-]+(?:/[\w-]+)+\.?$", "parse_sd")]
    drop_attributes = {"facebook", "twitter"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        geometry = loads(response.xpath('//script[contains(text(), "latitude")]/text()').get())["credentialSubject"][
            "geo"
        ]
        item["lat"], item["lon"] = geometry["latitude"], geometry["longitude"]
        apply_category(Categories.SHOP_SHOES, item)
        yield item
