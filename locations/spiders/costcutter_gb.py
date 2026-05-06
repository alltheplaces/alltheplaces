import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CostcutterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "costcutter_gb"
    item_attributes = {"brand": "Costcutter", "brand_wikidata": "Q5175072"}
    allowed_domains = ["costcutter.co.uk"]
    sitemap_urls = ["https://store-locator.costcutter.co.uk/sitemap.xml"]
    sitemap_rules = [(r"uk/en-gb/[^/]+/[^/]+/(\d+)$", "parse")]
    wanted_types = ["FoodEstablishment"]
    drop_attributes = {"image"}
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if img := response.xpath('//source[contains(@srcset, "api.mapbox.com")]/@srcset').get():
            if m := re.search(r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", img):
                item["lon"], item["lat"] = m.groups()

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
