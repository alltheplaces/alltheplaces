from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DelkoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "delko_fr"
    contacts = ["team.marketing@delko.com"]
    item_attributes = {"brand": "Delko", "brand_wikidata": "Q24934757"}
    sitemap_urls = ["https://www.delko.com/robots.txt"]
    sitemap_rules = [(r"com/garages/[^/]+$", "parse")]
    wanted_types = ["AutoRepair"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("DELKO ")

        item["lat"] = ld_data["latitude"]
        item["lon"] = ld_data["longitude"]
        item["extras"]["start_date"] = ld_data["foundingDate"]

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
