import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

ADDRESS_RE = re.compile(r"^(?P<city>.*?),\s*(?P<state>[A-Z]{2})(\s+(?P<postcode>\d{5}))?$")
POSTCODE_RE = re.compile(r"(\d{5})(-\d{4})?$")


class BiscuitvilleUSSpider(Spider):
    name = "biscuitville_us"
    item_attributes = {"brand": "Biscuitville", "brand_wikidata": "Q4917274"}
    allowed_domains = ["biscuitville.com"]
    start_urls = ["https://biscuitville.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css(".dealer-listings-grid.desktop .loop-item-wrapper"):
            hours_text = location.css(".details p")[1].xpath("string()").get("").strip()
            if "Closed" in hours_text:
                continue

            item = Feature()
            item["ref"] = item["website"] = location.css(".contact a::attr(href)").get()
            item["lat"] = location.css(".contact::attr(data-lat)").get()
            item["lon"] = location.css(".contact::attr(data-lng)").get()
            item["street_address"] = location.css(".contact .title::text").get("").strip()
            item["phone"] = location.css(".contact .phone::text").get()

            address_text = location.css(".contact .address::text").get("").strip()
            if m := ADDRESS_RE.match(address_text):
                item["city"] = m.group("city")
                item["state"] = m.group("state")
                item["postcode"] = m.group("postcode")
            if not item.get("postcode"):
                caddress = location.css(".contact::attr(data-caddress)").get("")
                if m := POSTCODE_RE.search(caddress):
                    item["postcode"] = m.group(1)

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

            apply_category(Categories.FAST_FOOD, item)

            yield item
