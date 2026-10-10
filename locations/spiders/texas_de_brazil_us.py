import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The locations page carries a window.locationsData array of map pins, each
# with the restaurant's page. Those pages hold a schema.org Restaurant record
# with a clean address, coordinates, phone and hours.
#
# The chain also operates outside the US, so records are filtered on the
# record's own addressCountry. Restaurants that have not opened yet have no
# Restaurant record at all and are skipped by the wanted type.


class TexasDeBrazilUSSpider(StructuredDataSpider):
    name = "texas_de_brazil_us"
    item_attributes = {"brand": "Texas de Brazil", "brand_wikidata": "Q7708244"}
    allowed_domains = ["texasdebrazil.com"]
    start_urls = ["https://texasdebrazil.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        if not (locations := re.search(r"window\.locationsData\s*=\s*", response.text)):
            self.logger.error("No locations on the locations page")
            return

        for location in chompjs.parse_js_object(response.text[locations.end() :]):
            if url := location.get("permalink"):
                yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        if ((ld_data.get("address") or {}).get("addressCountry") or "").upper() != "US":
            return

        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # "Texas de Brazil - Baton Rouge"
        item["branch"] = (item.pop("name", None) or "").split(" - ", 1)[-1].strip()
        # The url carries campaign parameters, and the description is the same
        # on every page.
        item["website"] = response.url
        item["extras"].pop("description", None)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "brazilian;steak_house"

        yield item
