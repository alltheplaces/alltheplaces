from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class KolacheFactoryUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kolache_factory_us"
    item_attributes = {"brand": "Kolache Factory"}
    allowed_domains = ["locations.kolachefactory.com"]
    sitemap_urls = ["https://locations.kolachefactory.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.kolachefactory\.com/[a-z]{2}/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.replace("https://locations.kolachefactory.com/", "")
        item["name"] = None
        item["branch"] = None
        # The description and photo are the same on every page.
        item["image"] = None
        item["extras"].pop("description", None)

        apply_category(Categories.SHOP_BAKERY, item)
        item["extras"]["cuisine"] = "kolache"

        yield item
