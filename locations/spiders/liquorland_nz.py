from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class LiquorlandNZSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "liquorland_nz"
    item_attributes = {"brand": "Liquorland", "brand_wikidata": "Q110295342"}
    sitemap_urls = ["https://www.liquorland.co.nz/content/sitemaps/sitemap-index.xml"]
    sitemap_rules = [(r"https://www.liquorland.co.nz/store-locations/[^/]+", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["image"] = None
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").replace("Liquorland ", "")
        item["website"] = response.url
        oh = OpeningHours()
        oh.add_ranges_from_string(",".join(ld_data["openingHours"]))
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
