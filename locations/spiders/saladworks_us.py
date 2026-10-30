from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SaladworksUSSpider(SitemapSpider, StructuredDataSpider):
    name = "saladworks_us"
    item_attributes = {"brand": "Saladworks", "brand_wikidata": "Q7403411"}
    allowed_domains = ["restaurants.saladworks.com"]
    sitemap_urls = ["https://restaurants.saladworks.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.saladworks\.com/[a-z]{2}/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("@id")
        item["branch"] = item.pop("name", None)
        # Every page carries the same brand photo.
        item["image"] = None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "salad"

        yield item
