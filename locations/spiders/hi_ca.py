from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HiCASpider(SitemapSpider, StructuredDataSpider):
    name = "hi_ca"
    item_attributes = {"brand": "Hostelling International", "brand_wikidata": "Q16984941"}
    sitemap_urls = ["https://hihostels.ca/en/sitemaps-1-section-hostels-1-sitemap.xml"]
    sitemap_rules = [("/en/hostels/", "parse")]
    wanted_types = ["Hostel"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("HI ")
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
