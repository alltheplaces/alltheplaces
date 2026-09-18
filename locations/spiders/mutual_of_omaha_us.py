from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MutualOfOmahaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mutual_of_omaha_us"
    item_attributes = {"name": "Mutual of Omaha", "brand": "Mutual of Omaha", "brand_wikidata": "Q17108173"}
    sitemap_urls = ["https://agents.mutualofomaha.com/sitemap.xml"]
    sitemap_rules = [(r"/district-offices/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removesuffix(" Mutual of Omaha Advisors")
        item["image"] = None
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
