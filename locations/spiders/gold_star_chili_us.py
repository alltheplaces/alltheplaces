import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The Yext location directory lists a page per restaurant in its sitemap, each
# carrying a schema.org FastFoodRestaurant record with address, coordinates,
# phone and hours.
#
# The city in those records runs two values together, e.g.
# "AlexandriaAlexandria" or "Mount OrabMt Orab", so it is read from the page
# URL instead.
#
# Every record shares the same marketing description and brand logo, so those
# are dropped.


class GoldStarChiliUSSpider(SitemapSpider, StructuredDataSpider):
    name = "gold_star_chili_us"
    item_attributes = {"brand": "Gold Star Chili", "brand_wikidata": "Q16994254"}
    allowed_domains = ["locations.goldstarchili.com"]
    sitemap_urls = ["https://locations.goldstarchili.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.goldstarchili\.com/([^/]+)$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("@id")
        item["name"] = None
        item["branch"] = None
        # The description and logo are the same on every page.
        item["image"] = None
        item["extras"].pop("description", None)

        # The record's city runs two values together, e.g. "AlexandriaAlexandria"
        # or "Mount OrabMt Orab", so it is taken from the page URL instead,
        # which is "<state>-<city>-<street>-<id>".
        if slug := re.fullmatch(r"[a-z]{2}-(.+?)-\d.*", response.url.rstrip("/").rsplit("/", 1)[-1]):
            item["city"] = slug.group(1).replace("-", " ").title()

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "chili"

        yield item
