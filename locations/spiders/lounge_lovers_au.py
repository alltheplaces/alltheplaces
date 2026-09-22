import json
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

STORE_LOCATOR_URL = "https://www.loungelovers.com.au/showrooms"


class LoungeLoversAUSpider(Spider):
    name = "lounge_lovers_au"
    item_attributes = {"brand": "Lounge Lovers", "brand_wikidata": "Q140684820"}
    allowed_domains = ["www.loungelovers.com.au"]
    start_urls = [STORE_LOCATOR_URL]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            re.search(r'([^"\\]+\.js[^"\\]*)\\"\],\\"ShowroomStoreLocator', response.text).group(1),
            callback=self.parse_server_action,
        )

    def parse_server_action(self, response: Response, **kwargs: Any) -> Any:
        # The showroom list is only reachable through a Next.js server action, whose
        # identifier changes with every deployment and so has to be read at run time.
        action_id = re.search(r'"([0-9a-f]{32,})"[^()]+"getStoreLocations"', response.text).group(1)
        yield Request(
            url=STORE_LOCATOR_URL,
            method="POST",
            headers={"Content-Type": "text/plain;charset=UTF-8", "Next-Action": action_id},
            body=json.dumps(
                [{"location": {"lat": -25.610111, "lng": 134.354806, "radius": 9999, "unit": "KM"}, "maxResults": 200}]
            ),
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for line in response.text.splitlines():
            _, _, payload = line.partition(":")
            if not payload.startswith("["):
                continue
            for location in json.loads(payload):
                location.update(location.pop("address"))
                item = DictParser.parse(location)
                item["branch"] = item.pop("name")
                item["street_address"] = item.pop("street")
                item["website"] = response.urljoin("/showrooms/" + location["url_key"])
                trading_hours = location.get("trading_hours") or {}
                if any(trading_hours.values()):
                    item["opening_hours"] = OpeningHours()
                    for day, hours in trading_hours.items():
                        if hours:
                            item["opening_hours"].add_range(day, *hours.split(" - "))
                        else:
                            item["opening_hours"].set_closed(day)
                apply_category(Categories.SHOP_FURNITURE, item)
                yield item
