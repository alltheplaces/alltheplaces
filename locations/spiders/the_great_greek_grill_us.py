import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The site runs on Popmenu, and its locations page carries every restaurant in
# one schema.org @graph of Restaurant records with address, coordinates, phone
# and hours.
#
# Restaurants that have not opened are marked "(Coming Soon!)" in their name,
# and usually in their branchCode too; either marker skips them.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class TheGreatGreekGrillUSSpider(StructuredDataSpider):
    name = "the_great_greek_grill_us"
    item_attributes = {"brand": "The Great Greek Mediterranean Grill"}
    allowed_domains = ["www.thegreatgreekgrill.com"]
    # Cloudflare answers 403 to many non-browser connections.
    requires_proxy = True
    start_urls = ["https://www.thegreatgreekgrill.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        name = ld_data.get("name") or ""
        branch_code = ld_data.get("branchCode") or ""
        if "coming soon" in name.lower() or "coming-soon" in branch_code:
            return

        item["ref"] = branch_code
        # "The Great Greek Mediterranean Grill® - Rosedale Hwy, CA", though a few
        # records carry only the branch, e.g. "Ocala, FL".
        item["branch"] = re.sub(r",\s*[A-Z]{2}$", "", name.split(" - ", 1)[-1]).strip()
        item["name"] = None
        # Every record points at the home page and shares the same photos.
        item["website"] = None
        item["image"] = None
        # Some records list several comma separated addresses, the chain's
        # shared inbox among them; the restaurant's own one is kept.
        if emails := [e.strip() for e in (item.get("email") or "").split(",") if e.strip()]:
            item["email"] = next((e for e in emails if not e.lower().startswith("info@")), emails[0])

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "greek;mediterranean"

        yield item
