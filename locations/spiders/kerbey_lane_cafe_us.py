from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The locations page links to a page per restaurant, each carrying a schema.org
# Restaurant record with address, phone and hours.
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class KerbeyLaneCafeUSSpider(StructuredDataSpider):
    name = "kerbey_lane_cafe_us"
    item_attributes = {"brand": "Kerbey Lane Cafe"}
    allowed_domains = ["www.kerbeylanecafe.com"]
    start_urls = ["https://www.kerbeylanecafe.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath("//a/@href").re(r"^/locations/[a-z0-9-]+$"))):
            yield response.follow(path, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # "Kerbey Lane Cafe Central"
        item["branch"] = (item.pop("name", None) or "").removeprefix("Kerbey Lane Cafe").strip()
        item["website"] = response.url

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "breakfast;american"

        yield item
