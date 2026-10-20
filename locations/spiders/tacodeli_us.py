from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Location pages come from the locator subdomain's sitemap, which also lists
# the directory pages, so only the two level paths are followed.
#
# Each page carries a schema.org Restaurant record with address, coordinates,
# phone, hours and an amenityFeature list.
#
# The record's name is the brand, so the branch comes from the page heading,
# whose first line is also the brand.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class TacodeliUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tacodeli_us"
    item_attributes = {"brand": "Tacodeli"}
    allowed_domains = ["locations.tacodeli.com"]
    sitemap_urls = ["https://locations.tacodeli.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.tacodeli\.com/locations/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.replace("https://locations.tacodeli.com/locations/", "")
        item["name"] = None
        item["branch"] = (response.xpath("//h1//text()").getall() or [None])[-1]
        item["website"] = response.url
        # The description is marketing copy and sameAs is the brand's own social
        # accounts and app listings.
        item["extras"].pop("description", None)
        item["facebook"] = None

        if any(
            "gender neutral" in (amenity.get("name") or "").lower() for amenity in ld_data.get("amenityFeature") or []
        ):
            item["extras"]["toilets:unisex"] = "yes"

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mexican;tacos"

        yield item
