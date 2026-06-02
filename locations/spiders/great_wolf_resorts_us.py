from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class GreatWolfResortsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "great_wolf_resorts_us"
    item_attributes = {"name": "Great Wolf Lodge", "brand": "Great Wolf Lodge", "brand_wikidata": "Q5600260"}
    allowed_domains = ["www.greatwolf.com"]
    sitemap_urls = ["https://www.greatwolf.com/php-root.sitemap.xml"]
    sitemap_rules = [(r"/customer-service$", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Any, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item.pop("facebook")
        item.pop("twitter")
        item["branch"] = item.pop("name").removeprefix("Great Wolf Lodge ")

        apply_category({"leisure": "water_park"}, item)
        yield item
