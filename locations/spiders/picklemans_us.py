import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Location pages come from the site's location sitemap and carry a schema.org
# Restaurant record with address, coordinates, phone and hours.
#
# Each page also has a second, hand written LocalBusiness block that is broken
# with <br /> tags and cannot be parsed; only the Restaurant record is used.
# A handful of records have no geo block, so those features have no geometry.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class PicklemansUSSpider(SitemapSpider, StructuredDataSpider):
    name = "picklemans_us"
    item_attributes = {"brand": "Pickleman's Gourmet Cafe"}
    allowed_domains = ["www.picklemans.com"]
    sitemap_urls = ["https://www.picklemans.com/location-sitemap.xml"]
    sitemap_rules = [(r"/location/([^/]+)/$", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # "Pickleman's Gourmet Cafe - Fayetteville, AR"
        item["branch"] = (item.pop("name", None) or "").split(" - ", 1)[-1].rsplit(",", 1)[0].strip()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # The image is the brand logo and sameAs the chain's own Facebook page.
        item["image"] = None
        item["facebook"] = None

        # A couple of records put the whole address, and sometimes the phone,
        # into streetAddress: "5555 W. Sunset Ave, Springdale, AR 72762, ...".
        if not item.get("city") and (
            address := re.match(r"(.+?),\s*([^,]+),\s*([A-Z]{2})(?:\s+(\d{5}))?", item.get("street_address") or "")
        ):
            item["street_address"], item["city"], item["state"], postcode = address.groups()
            if postcode:
                item["postcode"] = postcode

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich;pizza"

        yield item
