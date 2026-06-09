from typing import Any, AsyncIterator

import chompjs
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_closed, set_social_media
from locations.react_server_components import parse_rsc


class BarnesAndNobleUSSpider(Spider):
    name = "barnes_and_noble_us"
    item_attributes = {"brand": "Barnes & Noble", "brand_wikidata": "Q795454"}
    allowed_domains = [
        "stores.barnesandnoble.com",
    ]

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("US", 15000):
            yield Request(
                url=f'https://stores.barnesandnoble.com/?searchText={city["name"]}'.replace(" ", "+"),
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join(s for n, s in objs if isinstance(s, str)).encode()
        data = dict(parse_rsc(rsc))
        for store in (DictParser.get_nested_key(data, "stores") or {}).get("content", []):
            item = DictParser.parse(store)
            item.pop("twitter", None)
            # When both address1, address2 fields are present, address1 is venue/mall name else street address.
            item["street_address"] = store.get("address2") or store.get("address1")
            item["branch"] = item.pop("name")
            item["website"] = f'https://stores.barnesandnoble.com/store/{item["ref"]}'
            item["extras"]["start_date"] = store.get("openDate")
            if "closed" in store.get("message", "").lower():
                set_closed(item, store.get("closeDate"))

            store_hours = store.get("hoursList", [])
            if "Opening" in store.get("hours", "").title():  # opening soon
                continue
            try:
                item["opening_hours"] = self.parse_opening_hours(store_hours)
            except:
                self.logger.error(f"Failed to parse opening hours: {store_hours}")
                item["opening_hours"] = None
            if instagram := store.get("instagramLink"):
                set_social_media(item, SocialMedia.INSTAGRAM, instagram)
            apply_yes_no("second_hand", item, store.get("usedBook"))
            apply_category(Categories.SHOP_BOOKS, item)
            yield item

    def parse_opening_hours(self, hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            day = rule["dayName"]
            if open := rule.get("openTime"):
                if close := rule.get("closeTime"):
                    if "Closed" in open:
                        oh.set_closed(day)
                    else:
                        oh.add_range(
                            day,
                            open + " AM",
                            close + " PM",
                            time_format="%I:%M %p",
                        )
        return oh
