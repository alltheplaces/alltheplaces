import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class FamousFootwearSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://ecomprdsharedstorage.blob.core.windows.net/sitemaps/20000/stores-sitemap.xml"]
    wanted_types = ["Store"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        matches = re.search(r'location: \["(.*)", "(.*)"\],', response.text)
        item["lat"], item["lon"] = matches[1], matches[2]

        oh = OpeningHours()
        if raw_hours := ld_data.get("openingHours"):
            for rule in raw_hours:
                day, times = rule.split(" ", 1)
                open_time, close_time = times.split(" - ")
                oh.add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M%p")

        item["opening_hours"] = oh
        apply_category(Categories.SHOP_SHOES, item)

        yield item
