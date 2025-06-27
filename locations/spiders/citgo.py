from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CitgoSpider(SitemapSpider, StructuredDataSpider):
    name = "citgo"
    item_attributes = {"brand": "Citgo", "brand_wikidata": "Q2974437"}
    allowed_domains = ["citgo.com"]
    sitemap_urls = ["https://www.citgo.com/sitemap.xml"]
    sitemap_rules = [
        (r"/station-locator/locations/(\d+)", "parse_sd"),
    ]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.FUEL_STATION, item)
        yield item
