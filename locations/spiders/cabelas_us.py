import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CabelasUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cabelas_us"
    item_attributes = {"brand": "Cabela's", "brand_wikidata": "Q2793714"}
    allowed_domains = ["stores.cabelas.com"]
    sitemap_urls = ["https://stores.cabelas.com/sitemap.xml"]
    sitemap_rules = [(r"https://stores\.cabelas\.com/[-\w]+", "parse_sd")]
    wanted_types = ["SportingGoodsStore", "Store"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("Cabela's").strip()

        if coords := re.search(
            r"yextDisplayCoordinate%22%3A%7B%22latitude%22%3A([\d.-]+)%2C%22longitude%22%3A([\d.-]+)", response.text
        ):
            item["lat"], item["lon"] = coords.groups()

        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
