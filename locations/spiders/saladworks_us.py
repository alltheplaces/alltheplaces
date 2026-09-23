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
# The record's name is the site or mall the restaurant sits in rather than the
# brand, so it is kept as the branch.


class SaladworksUSSpider(SitemapSpider, StructuredDataSpider):
    name = "saladworks_us"
    item_attributes = {"brand": "Saladworks", "brand_wikidata": "Q7403411"}
    allowed_domains = ["restaurants.saladworks.com"]
    sitemap_urls = ["https://restaurants.saladworks.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.saladworks\.com/[a-z]{2}/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
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
