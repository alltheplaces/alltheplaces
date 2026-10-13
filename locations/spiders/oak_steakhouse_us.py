from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The home page links to a page per restaurant, each carrying a schema.org
# FoodEstablishment record with the address, phone and hours already in OSM
# syntax.
#
# The record's description is a page of marketing copy, and no coordinates are
# published.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class OakSteakhouseUSSpider(StructuredDataSpider):
    name = "oak_steakhouse_us"
    item_attributes = {"brand": "Oak Steakhouse"}
    allowed_domains = ["www.oaksteakhouse.com"]
    start_urls = ["https://www.oaksteakhouse.com/"]
    wanted_types = ["FoodEstablishment"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath("//a/@href").re(r"^/location/[a-z0-9-]+/$"))):
            yield response.follow(path, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name", None)
        item["website"] = response.url
        item["extras"].pop("description", None)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"

        yield item
