import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DrummondGolfAUSpider(SitemapSpider, StructuredDataSpider):
    name = "drummond_golf_au"
    item_attributes = {"brand": "Drummond Golf", "brand_wikidata": "Q124065894"}
    sitemap_urls = ["https://drummondgolf.com.au/sitemap.xml"]
    sitemap_rules = [("/pages/stores/", "parse_sd")]
    wanted_types = ["Organization"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("street_address"):
            if coords := re.search(r"\"(-?\d+\.\d+),\s?(-?\d+\.\d+)\"", response.xpath("//@data-markers").get("")):
                item["lat"], item["lon"] = coords.groups()
            item["phone"] = None
            item["branch"] = response.xpath("//title/text()").get().removesuffix(" Drummond Golf")
            item["website"] = response.url
            apply_category(Categories.SHOP_SPORTS, item)
            yield item
