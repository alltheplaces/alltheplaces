from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BarberitosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "barberitos_us"
    item_attributes = {"brand": "Barberitos", "brand_wikidata": "Q4859607"}
    allowed_domains = ["restaurants.barberitos.com"]
    sitemap_urls = ["https://restaurants.barberitos.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.barberitos\.com/[a-z]{2}/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("@id")
        item["branch"] = item.pop("name", None)
        # The logo is the brand's and the photo is a stock shot of the food.
        item["image"] = None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mexican"

        yield item
