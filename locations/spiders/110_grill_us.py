from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The site runs on Popmenu, and its locations page carries every restaurant in
# one schema.org @graph of Restaurant records with address, coordinates, phone
# and hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class OnehundredtenGrillUSSpider(StructuredDataSpider):
    name = "110_grill_us"
    item_attributes = {"brand": "110 Grill"}
    allowed_domains = ["www.110grill.com"]
    start_urls = ["https://www.110grill.com/locations"]
    # Popmenu sites sit behind Cloudflare, which answers 403 to many
    # non-browser connections.
    requires_proxy = True
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = ld_data.get("branchCode")
        # "110 Grill - Southington, CT"
        item["branch"] = (item.pop("name", None) or "").removeprefix("110 Grill - ").rsplit(",", 1)[0].strip()
        # Every record points at the home page and shares the same photos.
        item["website"] = None
        item["image"] = None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "american"

        yield item
