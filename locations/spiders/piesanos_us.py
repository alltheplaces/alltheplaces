from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The locations page links to a page per restaurant, each carrying a schema.org
# Restaurant record with address, coordinates, phone and hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class PiesanosUSSpider(StructuredDataSpider):
    name = "piesanos_us"
    item_attributes = {"brand": "Piesanos Stone Fired Pizza"}
    allowed_domains = ["piesanos.com"]
    start_urls = ["https://piesanos.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in sorted(set(response.xpath("//a/@href").re(r"^https://piesanos\.com/locations/[a-z0-9-]+/$"))):
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = ld_data.get("branchCode")
        item["name"] = None
        item["website"] = response.url

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza;italian"

        yield item
