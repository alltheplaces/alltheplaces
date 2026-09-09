from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class SportingLifeCASpider(SitemapSpider, StructuredDataSpider):
    name = "sporting_life_ca"
    item_attributes = {"brand": "Sporting Life", "brand_wikidata": "Q7579583"}
    sitemap_urls = ["https://locations.sportinglife.ca/sitemap.xml"]
    sitemap_rules = [(r"https://locations\.sportinglife\.ca/[-\w]+$", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["image"] = item["email"] = None
        if "closed" in item["name"].lower():
            set_closed(item)
        else:
            item["branch"] = item.pop("name").removeprefix("Sporting Life - ")
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
