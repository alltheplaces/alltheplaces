from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZoupUSSpider(SitemapSpider, StructuredDataSpider):
    name = "zoup_us"
    item_attributes = {"brand": "Zoup!"}
    allowed_domains = ["restaurants.zoup.com"]
    sitemap_urls = ["https://restaurants.zoup.com/sitemap_index.xml"]
    sitemap_rules = [
        (r"^https://restaurants\.zoup\.com/(?:co|de|il|in|mi|oh|pa)/[^/]+/[^/]+/$", "parse_sd"),
    ]
    wanted_types = ["FastFoodRestaurant"]
    search_for_email = False
    search_for_facebook = False
    search_for_image = False
    search_for_instagram = False
    search_for_twitter = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("@id")
        item["branch"] = item.pop("name", "").removeprefix("Zoup! Eatery & Frutta Bowls ").removeprefix("Zoup! Eatery ")
        item["image"] = None
        apply_category(Categories.FAST_FOOD, item)
        yield item
