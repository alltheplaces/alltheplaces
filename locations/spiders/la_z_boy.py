import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# La-Z-Boy's store finder (https://www.la-z-boy.com/storeLocator/storeLocator.jsp)
# lists three kinds of location: La-Z-Boy branded "Furniture Galleries"
# (businessType 004, a mix of company-owned and independently licensed
# dealers all trading as "La-Z-Boy"), "Comfort Studio" shop-in-shops hosted
# inside another retailer's store (003), and "Other Retailer" listings for
# unrelated furniture stores that merely stock some La-Z-Boy product (001).
# Only 004 stores get their own page on la-z-boy.com, and only those pages
# are listed in this sitemap, so it already gives just the La-Z-Boy branded
# storefronts without any extra filtering.
# Each store page itself renders its details client side from a Yext
# Knowledge API location document, fetched here directly.


class LaZBoySpider(Spider):
    name = "la_z_boy"
    item_attributes = {"brand": "La-Z-Boy", "brand_wikidata": "Q6391583"}
    start_urls = ["https://www.la-z-boy.com/img/storepages.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            if match := re.search(r"/store/(\w+)/", url):
                store_id = match.group(1)
                yield Request(
                    f"https://api.la-z-boy.com/api/location/{store_id}",
                    callback=self.parse_location,
                    cb_kwargs={"store_id": store_id},
                )

    def parse_location(self, response: Response, store_id: str, **kwargs: Any) -> Iterable[Feature]:
        location = response.json()
        if location.get("closed"):
            return

        item = DictParser.parse(location)
        item["ref"] = store_id
        item["street_address"] = " ".join(
            filter(None, [location["address"].get("line1"), location["address"].get("line2")])
        )
        item["website"] = f"https://www.la-z-boy.com/store/{store_id}/"
        item["phone"] = location.get("mainPhone")
        item["facebook"] = location.get("facebookPageUrl")
        item["extras"]["ref:google:place_id"] = location.get("googlePlaceId")

        oh = OpeningHours()
        for day_name, day_hours in location.get("hours", {}).items():
            # Non-day keys such as "holidayHours" and, for a store under a
            # temporary remodel closure, "reopenDate" (a plain string) can
            # also appear here.
            if not isinstance(day_hours, dict) or not day_hours.get("openIntervals"):
                continue
            for interval in day_hours["openIntervals"]:
                oh.add_range(day_name, interval["start"], interval["end"])
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
