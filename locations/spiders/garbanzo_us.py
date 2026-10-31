from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GarbanzoUSSpider(SitemapSpider, StructuredDataSpider):
    name = "garbanzo_us"
    item_attributes = {"brand": "Garbanzo Mediterranean Fresh"}
    allowed_domains = ["restaurants.eatgarbanzo.com"]
    sitemap_urls = ["https://restaurants.eatgarbanzo.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.eatgarbanzo\.com/[a-z]{2}/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.replace("https://restaurants.eatgarbanzo.com/", "").strip("/")
        item["branch"] = item.pop("name", None)
        item["image"] = None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mediterranean"

        yield item
