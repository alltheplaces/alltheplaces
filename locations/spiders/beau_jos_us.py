from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The locations page links to a page per restaurant, each carrying a schema.org
# Restaurant record with address, coordinates, phone and hours.
#
# The record's name is a marketing title, so the branch comes from the page
# path.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BeauJosUSSpider(StructuredDataSpider):
    name = "beau_jos_us"
    item_attributes = {"brand": "Beau Jo's"}
    allowed_domains = ["www.beaujos.com"]
    start_urls = ["https://www.beaujos.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in sorted(set(response.xpath("//a/@href").re(r"^https://www\.beaujos\.com/locations/[a-z0-9-]+/$"))):
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # "Beau Jo's Pizza - Arvada, CO | Authentic Colorado-Style Pizza"
        item["name"] = None
        item["branch"] = item["ref"].replace("-", " ").title()
        item["website"] = response.url
        item["image"] = None
        # The Facebook page is the brand's, repeated on every location page.
        item["facebook"] = None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item
