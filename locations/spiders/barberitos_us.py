from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The SOCi location directory lists a page per restaurant in its sitemap,
# alongside the state and city index pages. Each restaurant page carries a
# schema.org FastFoodRestaurant record with address, coordinates, phone and
# hours.
#
# The record's name is the branch, and the same brand logo appears on every
# page.


class BarberitosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "barberitos_us"
    item_attributes = {"brand": "Barberitos", "brand_wikidata": "Q4859607"}
    allowed_domains = ["restaurants.barberitos.com"]
    sitemap_urls = ["https://restaurants.barberitos.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.barberitos\.com/[a-z]{2}/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
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
