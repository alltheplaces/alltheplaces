import json
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media


class BarnesAndNobleUSSpider(Spider):
    name = "barnes_and_noble_us"
    item_attributes = {"brand": "Barnes & Noble", "brand_wikidata": "Q795454"}
    allowed_domains = [
        "stores.barnesandnoble.com",
    ]

    def start_requests(self):
        for city in city_locations("US", 15000):
            yield Request(
                url=f'https://stores.barnesandnoble.com/?searchText={city["name"]}'.replace(" ", "+"),
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in (
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]
            .get("stores", {})
            .get("content", [])
        ):
            item = DictParser.parse(store)
            # When both address1, address2 fields are present, address1 is venue/mall name else street address.
            item["street_address"] = store.get("address2") or store.get("address1")
            item["branch"] = item.pop("name")
            item["website"] = f'https://stores.barnesandnoble.com/store/{item["ref"]}'
            store_hours = store.get("hoursList", [])
            if "Opening " in store.get("hours", "").title():  # opening soon
                return
            try:
                item["opening_hours"] = self.parse_opening_hours(store_hours)
            except:
                self.logger.error(f"Failed to parse opening hours: {store_hours}")
                item["opening_hours"] = None
            if instagram := store.get("instagramLink"):
                set_social_media(item, SocialMedia.INSTAGRAM, instagram)
            apply_yes_no("second_hand", item, store.get("usedBook"))
            yield item

    def parse_opening_hours(self, hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            oh.add_range(
                rule["dayName"],
                rule["openTime"] + " AM",
                rule["closeTime"] + " PM",
                time_format="%I:%M %p",
            )
        return oh
