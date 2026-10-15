from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GoldStarChiliUSSpider(SitemapSpider, StructuredDataSpider):
    name = "gold_star_chili_us"
    item_attributes = {"brand": "Gold Star Chili", "brand_wikidata": "Q16994254"}
    allowed_domains = ["locations.goldstarchili.com"]
    sitemap_urls = ["https://locations.goldstarchili.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.goldstarchili\.com/[a-z]{2}-[^/]+$", "parse")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_image = False
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("@id")
        item["branch"] = item.pop("name", None)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "chili"

        yield item
