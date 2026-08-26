from typing import Any

import chompjs
from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.react_server_components import parse_rsc
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class SoletraderGBSpider(CamoufoxSpider):
    name = "soletrader_gb"
    item_attributes = {"brand": "Soletrader", "brand_wikidata": "Q25101942"}
    start_urls = ["https://www.soletrader.co.uk/store-locator"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        payload = "".join(s for _, s in map(chompjs.parse_js_object, scripts) if isinstance(s, str))

        for location in DictParser.get_nested_key(dict(parse_rsc(payload.encode())), "locations"):
            if not location["code"].isdigit():
                continue  # Fulfilment regions, not shops.

            address = location["address"]
            item = DictParser.parse(address)
            item["ref"] = location["code"]
            item["branch"] = (
                location["label"].removeprefix("SOLETRADER OUTLET ").removeprefix("SOLETRADER ").removeprefix("SOLE ")
            )
            item["street_address"] = address["address2"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                hours = location["operatingHours"][day.lower()]
                if not hours["open"]:
                    item["opening_hours"].set_closed(DAYS_EN[day])
                    continue
                item["opening_hours"].add_range(DAYS_EN[day], hours["opening"], hours["closing"])

            apply_category(Categories.SHOP_SHOES, item)

            yield item
