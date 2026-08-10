from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class EuroCarPartsGBSpider(Spider):
    name = "euro_car_parts_gb"
    allowed_domains = ["www.eurocarparts.com"]
    start_urls = ["https://www.eurocarparts.com/store-locator"]
    item_attributes = {"brand": "Euro Car Parts", "brand_wikidata": "Q23782692"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))
        stores = DictParser.get_nested_key(data, "stores")

        for store in stores:
            if store.get("hideOnFrontEnd"):  # Warehouses, distribution centers, and closed stores
                continue
            coords = store["address"].get("coordinates")
            if not coords or coords.get("lat") is None:  # Test/placeholder entries with no location
                continue

            item = Feature()
            item["ref"] = store["code"]
            item["branch"] = store["name"]
            item["lat"] = coords["lat"]
            item["lon"] = coords["lon"]
            item["city"] = store["address"]["city"]
            item["postcode"] = store["address"]["postalCode"]
            item["country"] = store["address"]["country"]
            item["phone"] = store["address"]["phoneNumber"]
            item["website"] = f"https://www.eurocarparts.com/store-locator/{store['url']}"

            lines = [line for line in store["address"]["lines"] if line and line != "Euro Car Parts"]
            item["street_address"] = ", ".join(lines)

            item["opening_hours"] = OpeningHours()
            for entry in store.get("openingHours", []):
                if entry["start"] is None or entry["end"] is None:  # Closed days
                    item["opening_hours"].set_closed(DAYS[entry["dayOfWeek"]])
                    continue

                # start and end are seconds since midnight
                open_time = f"{entry['start'] // 3600:02}:{entry['start'] % 3600 // 60:02}"
                close_time = f"{entry['end'] // 3600:02}:{entry['end'] % 3600 // 60:02}"

                item["opening_hours"].add_range(DAYS[entry["dayOfWeek"]], open_time, close_time)

            apply_category(Categories.SHOP_CAR_PARTS, item)
            yield item
