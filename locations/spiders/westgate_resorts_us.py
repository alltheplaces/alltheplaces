from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The hotels page links to a page per resort, each carrying a schema.org Hotel
# record with address, coordinates and phone.
#
# The collection includes resorts in the Bahamas, Canada and Mexico, which are
# dropped on the record's own addressCountry.


class WestgateResortsUSSpider(StructuredDataSpider):
    name = "westgate_resorts_us"
    item_attributes = {"brand": "Westgate Resorts", "brand_wikidata": "Q7988847"}
    allowed_domains = ["www.westgateresorts.com"]
    start_urls = ["https://www.westgateresorts.com/hotels/"]
    wanted_types = ["Hotel"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in set(response.xpath("//a/@href").re(r"^/hotels/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+/$")):
            yield response.follow(path, callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        if ((ld_data.get("address") or {}).get("addressCountry") or "").upper() != "US":
            return

        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Some records give a resort.to short link as their url.
        item["website"] = response.url
        item["branch"] = (item.pop("name", None) or "").removeprefix("Westgate ").strip()
        # The image is the brand logo, and the email is the chain's rentals desk.
        item["image"] = None
        item["email"] = None
        # A hotel is always open, and the record's hours describe the front desk.
        item["opening_hours"] = None

        apply_category(Categories.HOTEL, item)

        yield item
